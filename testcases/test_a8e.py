from ..common import adb,qnx,images
from ..utils import read_yaml
import pytest

class TestUint_Panel():
    def setup_class(self):
        print("前置条件")

    def teardown_class(self):
        print("后置条件")
    @pytest.mark.parametrize("test_data", read_yaml.read_yaml('./config/config.yaml'))
    def test_01_spd(self,test_data):
        test_qnx = qnx.qnx(test_data["devices"],test_data["ip"],test_data["user"],test_data["passwd"])
        test_qnx.qnx_screenshot(test_data["qnx_screenshot_path"])
        test = adb.adb.adb_pull_image(test_data["devices"],
                                        test_data["adb_pull_source"],
                                        test_data["adb_pull_dest"])
        test_image=images.Images()
        test_result = test_image.compare_by_matrix_in_same_area(
                                                                test_data["input_images_path_spd"],
                                                                test,
                                                                test_data["image_position_spd"])
        assert test_result == None
'''
class TestUint_Warning():

    def setup_class(self):
        print("前置条件")

    def teardown_class(self):
        print("后置条件")

    def test_02_eps(self):
        test_qnx = qnx.qnx("1234567","192.168.118.2","root","")
        test_qnx.qnx_screenshot("/var/share/")
        test = adb.adb.adb_pull_image("1234567",
                                    "/data/nfs/nfs_share/screenshot.bmp",
                                    "./testdata/actual/")
        test_image=images.Images()
        test_result = test_image.compare_by_matrix_in_same_area("./testdata/expect/screenshot_warning.bmp",
                                                                test,
                                                                (711,24,1227,80))
        assert test_result == None
'''