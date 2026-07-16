from abc import ABC, abstractmethod
from typing import Optional
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_community.chat_models import ChatTongyi
from core.agent_utils.config_handler import rag_config
from config import Config

class BaseModelFactory(ABC):
    @abstractmethod
    def generate(self) -> Optional[Embeddings | BaseChatModel]:
        pass

class ChatModelFactory(BaseModelFactory):
    def generate(self) -> Optional[Embeddings | BaseChatModel]:
        return ChatTongyi(
            model=rag_config["chat_model_name"],
            api_key=Config.DASHSCOPE_API_KEY,
        )

class EmbeddingsFactory(BaseModelFactory):
    def generate(self) -> Optional[Embeddings | BaseChatModel]:
        return DashScopeEmbeddings(
            model=rag_config["embedding_model_name"],
            dashscope_api_key=Config.DASHSCOPE_API_KEY
        )

chat_model = ChatModelFactory().generate()
embedding_model = EmbeddingsFactory().generate()