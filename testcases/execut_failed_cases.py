import os
import time
import functools
from datetime import datetime
from cluster_autotest.common.adb import adb
from cluster_autotest.utils.read_yaml import read_yaml

def execut_failed_cases(func):
    """
    自定义装饰器,用于捕获执行失败用例
    parame: func: 函数名
    return: wrapper:返回wrapper函数
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        """
        用于捕获AssertionError异常
        """
        try:
            func(*args, **kwargs) # 执行测试用例
        except AssertionError:
            test_name = func.__name__  # 获取测试用例名称
            current_time = datetime.now()
            formatted_time = current_time.strftime("%Y%m%d-%H%M%S")
            local_path = './cluster_autotest/logs/' + test_name + formatted_time
            os.mkdir(local_path)
            export_android_log(local_path)
            export_qnx_log(local_path)
            raise#让异常继续传播
    return wrapper

def export_android_log(folder):
    """
    导出安卓log
    parame: folder: 文件夹名
    """
    devices = read_yaml('./cluster_autotest/config/config.yaml')["devices"]
    remote_path=read_yaml('./cluster_autotest/config/config.yaml')["android_log_path"]
    adb.adb_root(devices)
    time.sleep(1)
    adb.adb_pull(devices,remote_path,folder)

def export_qnx_log(folder):
    """
    导出qnxlog
    parame: folder: 文件夹名
    """
    devices = read_yaml('./cluster_autotest/config/config.yaml')["devices"]
    remote_path=read_yaml('./cluster_autotest/config/config.yaml')["qnx_log_path"]
    adb.adb_root(devices)
    time.sleep(1)
    adb.adb_pull(devices,remote_path,folder)