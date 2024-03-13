import json
from logger.logger import logger


def read_json(path):
    """
    读取json配置文件
    parame: yaml_file_path: yaml配置文件路径
    return: value: 以字典形式返回解析的配置文件数据
    """
    try:
        with open( path, "r",encoding="utf-8") as file:
            value = json.load(file)
        logger.info("{}配置字读取成功,读到的内容为{}".format(path,value))
        return value
    except Exception as e:
            logger.error(e)
            raise