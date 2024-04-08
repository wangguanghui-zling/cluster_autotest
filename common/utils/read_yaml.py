import yaml
from common.logger.logger import logger

def read_yaml(path):
    """
    读取yaml配置文件
    parame: yaml_file_path: yaml配置文件路径
    return: value: 以字典形式返回解析的配置文件数据
    """
    try:
        with open( path, "r",encoding="utf-8") as f:
            value = yaml.load(stream=f, Loader=yaml.FullLoader)
        #except:
            #with open(yaml_file_path, "r",encoding="gbk") as f:
                #value = yaml.load(stream=f, Loader=yaml.FullLoader)
        logger.info("{}配置字读取成功,读到的内容为{}".format(path,value))
        return value
    except Exception as e:
            logger.error(e)
            raise