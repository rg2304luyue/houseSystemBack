"""
react_agent.py - 完整版 ReAct Agent
包含：房源工具 + MCP扩展工具 + RAG知识库工具
"""

from langchain.agents import create_agent
from core.agent_model.factor import chat_model
from core.agent_utils.prompt_loader import load_system_prompt
# 房源核心工具
from core.agent.tools.agent_tools import search_houses_by_criteria, get_house_details, get_popular_houses
# MCP 扩展工具
from core.agent.tools.mcp_tools import (
    get_weather_for_visit,
    search_nearby_facilities,
    calculate_commute_time,
    get_rental_market_tips
)
# 中间件
from core.agent.tools.middleware import monitor_tool, log_before_model, report_prompt_switch
import logging

logger = logging.getLogger(__name__)

# 构建 RAG 工具（懒加载，避免启动时报错）
def _build_rag_tool():
    """构建 RAG 知识库检索工具，加载失败时返回 None"""
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
        # 构建工具列表
        tools = [
            # 核心房源工具
            search_houses_by_criteria,
            get_house_details,
            get_popular_houses,
            # MCP 扩展工具
            get_weather_for_visit,
            search_nearby_facilities,
            calculate_commute_time,
            get_rental_market_tips,
        ]

        # 尝试加载 RAG 工具
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
        """非流式执行（供普通 /chat 接口调用）"""
        if history is None:
            history = []

        messages = history + [{"role": "user", "content": query}]
        input_dict = {"messages": messages}

        latest_message = None
        for chunk in self.agent.stream(input_dict, stream_mode="values", context={"report": False}):
            latest_message = chunk["messages"][-1]

        return latest_message.content if latest_message else "抱歉，暂时无法回答。"

    def execute_stream_with_history(self, query: str, history: list = None):
        """流式执行（供 SSE 接口调用）"""
        if history is None:
            history = []

        messages = history + [{"role": "user", "content": query}]
        input_dict = {"messages": messages}

        previous_content = ""
        try:
            for chunk in self.agent.stream(input_dict, stream_mode="values", context={"report": False}):
                latest = chunk["messages"][-1]
                if latest.content:
                    new_content = latest.content
                    if new_content.startswith(previous_content):
                        delta = new_content[len(previous_content):]
                    else:
                        delta = new_content
                    previous_content = new_content
                    if delta:
                        yield delta
        except Exception as e:
            logger.error(f"[ReactAgent] 流式执行出错: {e}")
            yield f"\n\n[系统错误: {str(e)}]"

    def execute_stream(self, query: str):
        """原有流式方法（向后兼容）"""
        yield from self.execute_stream_with_history(query, history=[])


if __name__ == '__main__':
    agent = ReactAgent()
    print("=== 测试: 搜索岳麓区房源 ===")
    result = agent.execute("帮我找一套岳麓区2000元以内的房源")
    print(result)