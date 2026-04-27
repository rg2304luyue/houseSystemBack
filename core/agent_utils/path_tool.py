"""
提供统一路径
"""
import os

def get_project_root() -> str:
    """
    获取工程所在根目录
    :return: 字符串根目录
    """
    # 当前文件的绝对路径
    cur_file = os.path.abspath(__file__)
    # 获取工程的根目录
    cur_dir = os.path.dirname(cur_file)
    pro_root = os.path.dirname(cur_dir)

    return pro_root

def get_abs_path(relative_path: str) -> str:
    """
    传递相对路径，得到绝对路径
    :param relative_path:
    :return: 绝对路径
    """
    pro_root = get_project_root()
    return os.path.join(pro_root, relative_path)


