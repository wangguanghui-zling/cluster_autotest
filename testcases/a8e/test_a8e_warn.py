from common.adb import adb
from common.qnx import qnx
from common.images import Images
from utils import read_yaml
from testcases import execut_failed_cases
import pytest
import allure

class TestUint_Warning():
    def setup_class(self):
        print("前置条件")

    def teardown_class(self):
        print("后置条件")
    @execut_failed_cases.execut_failed_cases #捕获执行失败用例
    @pytest.mark.parametrize("test_data", [read_yaml.read_yaml('./config/config.yaml')]) #参数化装饰
    def test_02_eps(self,test_data):
        test_qnx = qnx(test_data["devices"],test_data["qnx_ip"],test_data["qnx_user"],test_data["qnx_passwd"])
        test_qnx.qnx_screenshot(test_data["qnx_screenshot_path"])
        test = adb.adb_pull_image(test_data["devices"],
                                    test_data["adb_pull_source"],
                                    test_data["adb_pull_dest"])
        test_image=Images()
        test_result = test_image.compare_by_matrix_in_same_area(test_data["input_images_path_eps"],
                                                                test,
                                                                test_data["image_position_eps"])
        allure.attach.file(test_data["input_images_path_eps"], name="预期结果", attachment_type=allure.attachment_type.BMP)
        allure.attach.file(test, name="实际结果", attachment_type=allure.attachment_type.BMP)
        assert test_result == None