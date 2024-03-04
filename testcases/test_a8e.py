from ..common import adb,qnx,images

import pytest
class TestUint_Panel():
    def setup_class(self):
        print("前置条件")

    def teardown_class(self):
        print("后置条件")
    
    def test_01_spd(self):
        try:
            test_qnx = qnx.qnx("1234567","192.168.118.2","root","")
            test_qnx.qnx_screenshot("/var/share/")
            test = adb.adb.adb_pull("1234567","/data/nfs/nfs_share/screenshot.bmp",
                                    "./testdata/actual/screenshot_spd.bmp")
            test_image=images.Images()
            test_result = test_image.compare_by_matrix_in_same_area(
                                                                    "./testdata/actual/screenshot_spd.bmp",
                                                                    "./testdata/expect/screenshot_spd.bmp",
                                                                    (818,245,1092,485))
            assert test_result == None
        except Exception as e:
                print(e)

class TestUint_Warning():

    def setup_class(self):
        print("前置条件")

    def teardown_class(self):
        print("后置条件")

    def test_02_eps(self):
        try:
            test_qnx = qnx.qnx("1234567","192.168.118.2","root","")
            test_qnx.qnx_screenshot("/var/share/")
            test = adb.adb.adb_pull("1234567",
                                    "/data/nfs/nfs_share/screenshot.bmp",
                                    "./testdata/actual/screenshot_warning.bmp")
            test_image=images.Images()
            test_result = test_image.compare_by_matrix_in_same_area("./testdata/actual/screenshot_warning.bmp",
                                                                    "./testdata/expect/screenshot_warning.bmp",
                                                                    (711,24,1227,80))
            assert test_result == None
        except Exception as e:
            print(e)