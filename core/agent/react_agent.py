from langchain.agents import create_agent
from core.agent_model.factor import chat_model
from core.agent_utils.prompt_loader import load_system_prompt
from core.agent.tools.agent_tools import (rag_summarize, get_weather, get_user_id,
                                     get_user_location, get_current_month, fill_context_for_report)
from core.agent.tools.middleware import monitor_tool, log_before_model, report_prompt_switch

class ReactAgent:
    def __init__(self):
        self.agent = create_agent(
            model=chat_model,
            system_prompt=load_system_prompt(),
            tools=[rag_summarize, get_weather, get_user_id,
                   get_user_location, get_current_month, fill_context_for_report],
            middleware=[monitor_tool, log_before_model, report_prompt_switch],
        )

    def execute_stream(self, query: str):
        input_dict = {
            "messages": [
                {"role": "user", "content": query}
            ]
        }

        # 第三个参数context就是上下文runtime中的信息，就是我们做提示词的切换
        for chunk in self.agent.stream(input_dict, stream_mode="values", context={"report": False}):
            latest_message = chunk["messages"][-1]  # 有历史记录所以取最后一条
            if latest_message.content:
                yield latest_message.content.strip() + "\n"

if __name__ == '__main__':
    agent = ReactAgent()
    for chunk in agent.execute_stream("给我生成我的使用报告"):
        print(chunk, end="", flush=True)