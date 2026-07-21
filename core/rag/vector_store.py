import os
from langchain_chroma import Chroma
from langchain_core.documents import Document
from core.agent_utils.config_handler import chroma_config
from core.agent_model.factor import get_embedding_model
from langchain_text_splitters import RecursiveCharacterTextSplitter
from core.agent_utils.path_tool import get_abs_path
from core.agent_utils.file_handler import pdf_loader, txt_loader, listdir_with_allowed_type, get_file_md5_hex
import logging
logger = logging.getLogger(__name__)

class VectorStoreService:
    def __init__(self):
        self.vector_store = Chroma(
            collection_name=chroma_config["collection_name"],
            embedding_function=get_embedding_model(),
            persist_directory=get_abs_path(chroma_config["persist_directory"]),
        )

        self.spliter = RecursiveCharacterTextSplitter(
            chunk_size=chroma_config["chunk_size"],
            chunk_overlap=chroma_config["chunk_overlap"],
            separators=chroma_config["separators"],
            length_function=len,
        )

    def get_retriever(self):
        return self.vector_store.as_retriever(search_kwargs={"k": chroma_config["k"]})

    def load_document(self):
        """
        从数据文件夹内读取数据文件, 转为向量存入向量数据库
        要计算文件的MD5做去重
        :return:
        """

        def check_md5(md5_for_check: str):
            if not os.path.exists(get_abs_path(chroma_config["md5_hex_store"])):
                # 创建文件
                open(get_abs_path(chroma_config["md5_hex_store"]), "w", encoding="utf-8").close()
                return False

            with open(get_abs_path(chroma_config["md5_hex_store"]), "r", encoding="utf-8") as f:
                for line in f.readlines():
                    line = line.strip()
                    if line == md5_for_check:
                        return True  # md5处理过

                return False         # md5没处理过

        def save_md5_hex(md5_for_check: str):
            with open(get_abs_path(chroma_config["md5_hex_store"]), "a", encoding="utf-8") as f:
                f.write(md5_for_check + "\n")

        def get_line_documents(read_path: str):
            if read_path.endswith("txt"):
                return txt_loader(read_path)

            if read_path.endswith("pdf"):
                return pdf_loader(read_path, None)

            return []

        allowed_files_path: list[str] = listdir_with_allowed_type(
            get_abs_path(chroma_config["data_path"]),
            tuple(chroma_config["allow_knowledge_file_type"]),
        )

        for path in allowed_files_path:
            # 获取文件md5
            md5_hex = get_file_md5_hex(path)

            if check_md5(md5_hex):
                logger.info(f"[加载数据库]{path}已存在")
                continue

            try:
                documents: list[Document] = get_line_documents(path)
                if not documents:
                    logger.warning(f"[加载数据库]{path}内没有有效内容, 跳过")
                    continue

                split_document: list[Document] = self.spliter.split_documents(documents)
                if not split_document:
                    logger.warning(f"[加载数据库]{path}分片后没有有效内容, 跳过")
                    continue

                # 将内容存入向量库
                self.vector_store.add_documents(split_document)

                # 记录这个已经处理过的md5_hex
                save_md5_hex(md5_hex)

                logger.info(f"[加载数据库]{path}内容加载成功")
            except Exception as e:
                # exc_info会记录详细报错信息
                logger.error(f"[加载数据库]{path}加载失败, {str(e)}", exc_info=True)

if __name__ == "__main__":
    vs = VectorStoreService()
    vs.load_document()
    retriever = vs.get_retriever()
    res = retriever.invoke("迷路")
    for doc in res:
        print(doc.page_content)
        print("="*10)
