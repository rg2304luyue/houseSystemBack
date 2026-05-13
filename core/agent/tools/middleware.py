from typing import Callable, Any
from langchain.agents import AgentState
from langchain.agents.middleware import wrap_tool_call, before_model, dynamic_prompt, ModelRequest
from langchain.tools.tool_node import ToolCallRequest
from langchain_core.messages import ToolMessage
from langgraph.runtime import Runtime
from langgraph.types import Command
from core.agent_utils.prompt_loader import load_system_prompt, load_report_prompt
import logging
logger = logging.getLogger(__name__)

MAX_TOOL_CALLS = 20  # 单次 Agent 运行最大工具调用次数


@wrap_tool_call
def monitor_tool(
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command],
) -> ToolMessage | Command:
    # 工具调用步数限制，防止无限循环
    count = request.runtime.context.get("_tool_call_count", 0) + 1
    request.runtime.context["_tool_call_count"] = count
    if count > MAX_TOOL_CALLS:
        logger.warning(f"[tool monitor] 工具调用次数已达上限 {MAX_TOOL_CALLS}，强制终止")
        raise RuntimeError(f"工具调用次数超过上限 ({MAX_TOOL_CALLS})，已终止以避免无限循环。请缩小问题范围后重试。")

    logger.info(f"[tool monitor] 执行工具({count}/{MAX_TOOL_CALLS}): {request.tool_call['name']}")
    logger.info(f"[tool monitor] 执行参数: {request.tool_call['args']}")
    try:
        result = handler(request)
        logger.info(f"[tool monitor] 工具{request.tool_call['name']}调用成功")

        if request.tool_call['name'] == 'fill_context_for_report':
            logger.info(f"[tool monitor] fill_context_for_report工具被调用，注入上下文 report=True")
            request.runtime.context["report"] = True
        return result
    except Exception as e:
        logger.info(f"工具{request.tool_call['name']}调用失败: {e}")
        raise e

@before_model
def log_before_model(
        state:AgentState,     # 整个Agent智能体中的状态记录
        runtime: Runtime      # 记录了整个执行过程中的上下文信息
) -> dict[str, Any] | None:
    logger.info(f"[log_before_model]: 即将调用模型，带有{len(state['messages'])}条消息，消息如下：")
    # for message in state['messages']:
    #     logger.info(f"[log_before_model][{type(message).__name__}]: {message.content.strip()}")
    logger.info(f"[log_before_model]: ----------省略已输出内容----------")
    logger.info(f"[log_before_model][{type(state['messages'][-1]).__name__}]: {state['messages'][-1].content.strip()}")


    return None

@dynamic_prompt                                          # 每一次在生成提示词之前调用此函数
def report_prompt_switch(request: ModelRequest) -> str:  # 动态切换提示词
    is_report = request.runtime.context.get("report", False)
    if is_report:                                        # 是报告生成路径，返回报告生成提示词内容
        return load_report_prompt()

    return load_system_prompt()