from common.adb import adb
from common.qnx import qnx
from common.can import CANoe
from utils import read_yaml
from common.images import Images
from testcases import execut_failed_cases
import pytest
import allure
import time

class TestUint_Panel():
    def setup_class(self):
        print("前置条件")
    def teardown_class(self):
        print("后置条件")
    @execut_failed_cases.execut_failed_cases
    @pytest.mark.parametrize("test_data", [read_yaml.read_yaml('./config/config.yaml')])
    def test_01_spd(self,test_data):
        app = CANoe() #定义CANoe为app
        app.open_cfg(test_data["cfg_path"]) #导入某个CANoe congif
        time.sleep(2)
        app.start_Measurement()
        time.sleep(3)
        test_qnx = qnx(test_data["devices"],test_data["qnx_ip"],test_data["qnx_user"],test_data["qnx_passwd"])
        test_qnx.qnx_screenshot(test_data["qnx_screenshot_path"])
        test = adb.adb_pull_image(test_data["devices"],
                                        test_data["adb_pull_source"],
                                        test_data["adb_pull_dest"])
        test_image=Images()
        test_result = test_image.compare_by_matrix_in_same_area(
                                                                test_data["input_images_path_spd"],
                                                                test,
                                                                test_data["image_position_spd"])
        allure.attach.file(test_data["input_images_path_spd"], name="预期结果", attachment_type=allure.attachment_type.BMP)
        allure.attach.file(test, name="实际结果", attachment_type=allure.attachment_type.BMP)
        #app.close_cfg()
        assert test_result == None