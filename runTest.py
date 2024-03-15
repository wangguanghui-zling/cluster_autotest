import os
import pytest
import threading
from common.images import Images
from common.video import *
from utils.read_yaml import read_yaml
from testcases import common

if __name__ == '__main__':
    pytest.main([
                "-q",
                "-s", 
                "-ra", 
                r".\testcases\a8e",
                '--alluredir',
                r'.\reports',
                '--clean-alluredir'
                ])
    #方式一：直接打开默认浏览器展示报告
    #allure serve ./result/
    #方式二：从结果生成报告
    #生成报告
    #allure generate ./result/ -o ./report/ --clean (覆盖路径加--clean)
    #打开报告
    #allure open -h 127.0.0.1 -p 8883 ./report/
    os.system(r'allure serve .\reports')