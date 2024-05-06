from common.adb.adb import adb
from common.qnx.qnx import qnx
from common.can.canoe import CANoe
from common.utils import read_yaml
from common.utils import read_excel
from common.images.images import Images
from common.utils import case_fail
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


    
    def teardown_class(self):
        adb.del_iviimage() #删除qnx侧截图
        adb.del_qnximage() #删除ivi侧截图


    @case_fail.execut_failed_cases
    @pytest.mark.parametrize("test_data", [read_excel.read_excel('./input/input_case/testdata.xlsx','test_01_spd')])
    def test_01_spd(self,test_data):
        # 获取信号
        sig_msg = (test_data["msgId"], test_data["sigName"],test_data["sigData"])
        print(f"sig_msg={sig_msg}")
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
                                                                test_data["预期结果"],
                                                                get_act_images,
                                                                position)
        #重置信号
        reset_signal = (test_data["msgId"], test_data["sigName"], 0)
        print(f"reset_signal={reset_signal}")
        allure.attach.file(test_data["预期结果"], name="预期结果", attachment_type=allure.attachment_type.BMP)
        allure.attach.file(get_act_images, name="实际结果", attachment_type=allure.attachment_type.BMP)
        assert test_result == None