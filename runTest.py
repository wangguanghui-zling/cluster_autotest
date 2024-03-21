import os
import pytest
from common.can import *
from common.images import Images
from common.video import *
from utils.read_yaml import read_yaml
from testcases import common
dbc_path = './common/canoe_project/A8E_Proj_IHU_PFET_CMX+V1.25_20230421.dbc'
data = [0,0,0,0,0,0,0,0]
message_id = 0x260
signal_name1 = 'BCS_VehSpd'
signal_name2 = 'BCS_VehSpdVD'
signal_value1 = 92
signal_value2 = 1
message_fram1=physical_to_frame(dbc_path,data,message_id,signal_name1,signal_value1)
message_fram2=physical_to_frame(dbc_path,message_fram1,message_id,signal_name2,signal_value2)
can_transmit(message_fram2,10)
#Close CAN 
ret=zcanlib.ResetCAN(chn_handle)
if ret==1:
    print("ResetCAN success! ")
#Close Device
ret=zcanlib.CloseDevice(handle)
if ret==1:
    print("CloseDevice success! ")

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