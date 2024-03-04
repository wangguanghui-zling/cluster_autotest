import pytest
import os

if __name__ == '__main__':
    pytest.main(["-q", "-s", "-ra", r"C:\Users\Administrator\Desktop\cluster_hmi\Project\testcases\test_a8e.py",'--alluredir',r'C:\Users\Administrator\Desktop\cluster_hmi\Project\reports'])
    #方式一：直接打开默认浏览器展示报告
    #allure serve ./result/
    #方式二：从结果生成报告
    #生成报告
    #allure generate ./result/ -o ./report/ --clean (覆盖路径加--clean)
    #打开报告
    #allure open -h 127.0.0.1 -p 8883 ./report/
    os.system(r'allure serve C:\Users\Administrator\Desktop\cluster_hmi\Project\reports')