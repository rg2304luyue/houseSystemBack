"""
react_agent.py - ReAct Agent
"""
import time
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, AIMessageChunk
from core.agent_model.factor import chat_model
from core.agent_utils.prompt_loader import load_system_prompt
from core.agent.tools.agent_tools import search_houses_by_criteria, get_house_details, get_popular_houses
from core.agent.tools.mcp_tools import (
    get_weather_for_visit,
    search_nearby_facilities,
    calculate_commute_time,
    get_rental_market_tips
)
from core.agent.tools.middleware import monitor_tool, log_before_model, report_prompt_switch
import logging

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_BASE_DELAY = 1.5
MAX_AGENT_STEPS = 20  # 最大工具调用步数，防止无限循环


def _build_rag_tool():
    try:
        from langchain_core.tools import tool
        from core.rag.rag_service import RagSummarizeService
        rag_service = RagSummarizeService()

        @tool(
            description="""
            从私有知识库中检索租房相关知识，包括：
            - 各区域（岳麓区、天心区、雨花区等）租房特点和租金行情
            - 租房流程和注意事项
            - 合同条款解读和签约建议
            - 押金相关规定
            - 整租和合租的对比
            - 维修责任划分
            - 租房纠纷处理方法
            - 看房检查清单
            适用于回答租房相关的政策、流程、常识性问题（不用于查询具体房源）
            """
        )
        def rag_summarize(query: str) -> str:
            try:
                logger.info(f"[Tool:RAG] 知识库查询: {query}")
                result = rag_service.rag_summarize(query)
                logger.info(f"[Tool:RAG] 查询完成，结果长度: {len(result)}")
                return result
            except Exception as e:
                logger.error(f"[Tool:RAG] 查询失败: {e}")
                return f"知识库查询失败: {str(e)}"

        logger.info("[ReactAgent] RAG 知识库工具加载成功")
        return rag_summarize
    except Exception as e:
        logger.warning(f"[ReactAgent] RAG 工具加载失败（忽略）: {e}")
        return None


class ReactAgent:
    def __init__(self):
        tools = [
            search_houses_by_criteria,
            get_house_details,
            get_popular_houses,
            get_weather_for_visit,
            search_nearby_facilities,
            calculate_commute_time,
            get_rental_market_tips,
        ]

        rag_tool = _build_rag_tool()
        if rag_tool:
            tools.append(rag_tool)
        else:
            logger.warning("[ReactAgent] RAG 工具未加载，知识库功能不可用")

        self.agent = create_agent(
            model=chat_model,
            system_prompt=load_system_prompt(),
            tools=tools,
            middleware=[monitor_tool, log_before_model, report_prompt_switch],
        )
        logger.info(f"[ReactAgent] 初始化完成，加载工具 {len(tools)} 个")

    def execute(self, query: str, history: list = None) -> str:
        if history is None:
            history = []

        messages = history + [{"role": "user", "content": query}]
        input_dict = {"messages": messages}

        last_exception = None
        for attempt in range(MAX_RETRIES):
            try:
                latest_message = None
                for chunk in self.agent.stream(input_dict, stream_mode="values", context={"report": False}):
                    latest_message = chunk["messages"][-1]

                return latest_message.content if latest_message else "抱歉，暂时无法回答。"

            except Exception as e:
                last_exception = e
                logger.warning(f"[ReactAgent] 第 {attempt + 1} 次执行失败: {e}")
                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_BASE_DELAY * (2 ** attempt)
                    time.sleep(delay)
                else:
                    logger.error(f"[ReactAgent] {MAX_RETRIES} 次重试后仍失败: {e}")

        return f"抱歉，服务暂时不可用，请稍后重试。（错误: {str(last_exception)}）"

    def execute_stream_with_history(self, query: str, history: list = None):
        if history is None:
            history = []

        messages = history + [{"role": "user", "content": query}]
        input_dict = {"messages": messages}

        sent_length = 0
        try:
            for chunk in self.agent.stream(input_dict, stream_mode="values", context={"report": False}):
                latest = chunk["messages"][-1]

                if not isinstance(latest, AIMessage):
                    continue

                if getattr(latest, 'tool_calls', None):
                    continue

                if not latest.content:
                    continue

                content = latest.content
                if len(content) > sent_length:
                    delta = content[sent_length:]
                    sent_length = len(content)
                    yield delta

        except Exception as e:
            logger.error(f"[ReactAgent] 流式执行出错: {e}")
            yield f"\n\n[系统错误: {str(e)}]"

    def execute_stream(self, query: str):
        yield from self.execute_stream_with_history(query, history=[])
