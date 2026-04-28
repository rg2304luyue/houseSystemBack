from langchain.agents import create_agent
from core.agent_model.factor import chat_model
from core.agent_utils.prompt_loader import load_system_prompt
# 导入我们新写的房产工具
from core.agent.tools.agent_tools import search_houses_by_criteria, get_house_details, get_popular_houses
from core.agent.tools.middleware import monitor_tool, log_before_model, report_prompt_switch


class ReactAgent:
    def __init__(self):
        self.agent = create_agent(
            model=chat_model,
            system_prompt=load_system_prompt(),
            # 注册房产工具
            tools=[search_houses_by_criteria, get_house_details, get_popular_houses],
            middleware=[monitor_tool, log_before_model, report_prompt_switch],
        )

    def execute(self, query: str, history: list = None):
        """新增的非流式执行方法，供 Flask 接口调用"""
        if history is None:
            history = []

        messages = history + [{"role": "user", "content": query}]
        input_dict = {
            "messages": messages
        }

        # 运行 agent 并获取最终结果，带上原本底层的 context 防报错
        for chunk in self.agent.stream(input_dict, stream_mode="values", context={"report": False}):
            latest_message = chunk["messages"][-1]

        return latest_message.content

    def execute_stream(self, query: str):
        """你原来保留的流式输出方法"""
        input_dict = {
            "messages": [
                {"role": "user", "content": query}
            ]
        }
        for chunk in self.agent.stream(input_dict, stream_mode="values", context={"report": False}):
            latest_message = chunk["messages"][-1]
            if latest_message.content:
                yield latest_message.content.strip() + "\n"

if __name__ == '__main__':
    agent = ReactAgent()
    for chunk in agent.execute_stream("给我生成我的使用报告"):
        print(chunk, end="", flush=True)