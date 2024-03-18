from common.adb import adb
from common.qnx import qnx
from common.can import CANoe
from utils import read_yaml
from utils import read_excel
from common.images import Images
from testcases import execut_failed_cases
import pytest
import allure
import time

class TestUint_Panel():

    def setup_class(self):
        #启动CANoe并连接仪表
        self.config_data=read_yaml.read_yaml('./config/config.yaml')
        self.app = CANoe() #定义CANoe为app
        self.app.open_cfg(self.config_data["cfg_path"]) #导入某个CANoe congif
        self.app.start_Measurement()
        time.sleep(3)
        self.test_qnx = qnx(self.config_data["devices"],self.config_data["qnx_ip"],self.config_data["qnx_user"],self.config_data["qnx_passwd"])


    @pytest.mark.parametrize("test_data", [read_excel.read_excel('./testdata/testdata.xlsx', 'test_01_spd')])
    def teardown_class(self, test_data):
        reset_signal = (test_data["msgId"], test_data["sigName"], 0) #重置信号
        adb.del_iviimage() #删除qnx侧截图
        adb.del_qnximage() #删除ivi侧截图


    @execut_failed_cases.execut_failed_cases
    @pytest.mark.parametrize("test_data", [read_excel.read_excel('./testdata/testdata.xlsx','test_01_spd')])
    def test_01_spd(self,test_data):
        # 获取信号
        sig_msg = (test_data["msgId"], test_data["sigName"],test_data["sigData"])
        #发送信号
        # 获取仪表截图
        self.test_qnx.qnx_screenshot(self.config_data["qnx_screenshot_path"])
        get_act_images = adb.adb_pull_image(self.config_data["devices"],
                           self.config_data["adb_pull_source"],
                           self.config_data["adb_pull_dest"])
        # 获取预期图坐标
        position = (test_data["startx"],test_data["starty"],test_data["endx"],test_data["endy"])
        # 实际图与预期图进行对比
        test_image=Images()
        test_result = test_image.compare_by_matrix_in_same_area(
                                                                test_data["本地图片位置"],
                                                                get_act_images,
                                                                position)
        allure.attach.file(test_data["本地图片位置"], name="预期结果", attachment_type=allure.attachment_type.BMP)
        allure.attach.file(get_act_images, name="实际结果", attachment_type=allure.attachment_type.BMP)
        assert test_result == None