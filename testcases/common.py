import os
import cv2
import time
import threading
import functools
from datetime import datetime
from common.adb import adb
from logger.logger import logger
from utils.read_yaml import read_yaml


recording = False #视频录制状态标志位
config = read_yaml('./config/config.yaml') #加载配置文件

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
            local_path = './logs/' + test_name + formatted_time
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
    devices = config["devices"]
    remote_path=config["android_log_path"]
    adb.adb_root(devices)
    time.sleep(1)
    adb.adb_pull(devices,remote_path,folder)

def export_qnx_log(folder):
    """
    导出qnxlog
    parame: folder: 文件夹名
    """
    devices = config["devices"]
    remote_path=config["qnx_log_path"]
    adb.adb_root(devices)
    time.sleep(1)
    adb.adb_pull(devices,remote_path,folder)


def start_recording(file):
    """
    开始录制视频
    parame: file: 文件名
    """
    try:
        global recording
        cap=cv2.VideoCapture(config["camera_index"])
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        file_name = config["video_path"]+"\\"+file+"-"+time.strftime("%Y%m%d_%H%M%S", time.localtime())+".mp4"
        video_writer = cv2.VideoWriter(file_name, fourcc, config["video_fps"], (640, 480))
        recording = True
        logger.info("开始录制...{}".format(file_name))
        while recording:
            ret, frame = cap.read()
            if ret:
                video_writer.write(frame)
            else:
                break
        video_writer.release()
    except Exception as e:
        logger.error(e)

def stop_recording():
    """
    停止录制视频
    """
    try:
        global recording
        recording = False
        logger.info("停止录制")
    except Exception as e:
        logger.error(e)

def trigger_start_event(file):
    """
    触发开始录制事件,通过threading.Thread将start_recording方法添加到线程池,实现控制开启录制和停止录制
    parame: file: 文件名
    """
    global recording
    start_recording_thread = threading.Thread(target=start_recording,args=(file,))
    start_recording_thread.start()

def trigger_stop_event():
    """
    触发停止录制事件
    """
    global recording
    stop_recording()