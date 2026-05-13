"""
yaml
k: v
"""
import yaml
from core.agent_utils.path_tool import get_abs_path

def load_rag_config(config_path: str=get_abs_path('agent_config/rag.yaml'), encoding: str="utf-8"):
    with open(config_path, "r", encoding=encoding) as f:
        return yaml.safe_load(f)

def load_chroma_config(config_path: str=get_abs_path('agent_config/chroma.yaml'), encoding: str="utf-8"):
    with open(config_path, "r", encoding=encoding) as f:
        return yaml.safe_load(f)

def load_prompts_config(config_path: str=get_abs_path('agent_config/prompts.yaml'), encoding: str="utf-8"):
    with open(config_path, "r", encoding=encoding) as f:
        return yaml.safe_load(f)

def load_agent_config(config_path: str=get_abs_path('agent_config/agent.yaml'), encoding: str="utf-8"):
    with open(config_path, "r", encoding=encoding) as f:
        return yaml.safe_load(f)

rag_config = load_rag_config()
chroma_config = load_chroma_config()
prompts_config = load_prompts_config()
agent_config = load_agent_config()