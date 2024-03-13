from common.adb import adb
from common.qnx import qnx
from utils import read_yaml
from utils import read_excel
from common.can import CANoe
from common.images import Images
from testcases import execut_failed_cases
import pytest
import allure
import time

class TestUint_Warning():
    def setup_class(self):
        test_data=read_yaml.read_yaml('./config/config.yaml')
        test_qnx = qnx(test_data["devices"],test_data["qnx_ip"],test_data["qnx_user"],test_data["qnx_passwd"])
        test_qnx.qnx_screenshot(test_data["qnx_screenshot_path"])
        self.test = adb.adb_pull_image(test_data["devices"],
                                        test_data["adb_pull_source"],
                                        test_data["adb_pull_dest"])

    def teardown_class(self):
        print("后置条件")
    @execut_failed_cases.execut_failed_cases #捕获执行失败用例
    @pytest.mark.parametrize("test_data", [read_excel.read_excel('./testdata/testdata.xlsx','test_02_eps')])
    def test_02_eps(self,test_data):
        position = (test_data["startx"],test_data["starty"],test_data["endx"],test_data["endy"])
        test_image=Images()
        test_result = test_image.compare_by_matrix_in_same_area(test_data["本地图片位置"],
                                                                self.test,
                                                                position)
        allure.attach.file(test_data["本地图片位置"], name="预期结果", attachment_type=allure.attachment_type.BMP)
        allure.attach.file(self.test, name="实际结果", attachment_type=allure.attachment_type.BMP)
        assert test_result == None