#! /usr/bin/env python



"""
this module is a sub-process and mainly used for camera recording and taking picture
"""

import cv2 as cv
import multiprocessing
import queue
import os
import time
import datetime
import shutil
import numpy as np

ENABLE_LOGGER = True
if ENABLE_LOGGER:
    try:
        from common.logger.logger import logger
    except (ImportError, ModuleNotFoundError) as e:
        import logging as logger
else:
    def empty(): pass
    methods = {
        "error": empty,
        "warning": empty,
        "warn": empty,
        "info": empty,
        "debug": empty,
    }
    logger = type("logger", bases=(object, ), dict=methods)
from common.camera.cameraSetting import SETTINGS


class CameraProcess(multiprocessing.Process):
    def __init__(
            self,
            outputPath: str,
            queueW: multiprocessing.Queue,
            queueR: multiprocessing.Queue,
            cameraId: int = 0,
            resolution: (list, tuple) = (800, 600),
            fps: int = 20,
            videoSplit: int = 60,
            name: str = None,
            daemon: bool = True,
            cameraSet: dict = None,
            **kwargs
    ):
        """
        init a sub-process
        @param:
            outputPath: a path used for storing both videos and pictures taken from camera
            queueW: a queue objects used for communicate with main process, Write only
            queueR: a queue objects used for communicate with main process, Read only
            cameraId: camera id for a specific camera, if only one camera's available then 0 should be used
            resolution: resolution for camera or display, default to (800, 600)
            fps: frame rate per second, default to 30
            videoSplit: split video by time 'videoSplit', default to 60min
            name: name of sub-process
            daemon: set sub-process as a daemon or not, default to True
            cameraSet: "CAP_PROP_POS_MSEC", "CAP_PROP_POS_FRAMES" and etc, no "cv." as prefix, see SETTINGS
            kwargs: some other parameters
        """
        super().__init__(name=name, daemon=daemon)

        self.__outputPath = outputPath
        self.__queueR = queueW
        self.__queueW = queueR
        self.__cameraId = cameraId
        self.__resolution = resolution
        self.__fps = fps
        self.__videoSplit = videoSplit
        self.__cameraSet = cameraSet
        self.__kwargs = kwargs

        self.__cap = None
        self.__videoWriterObj = None
        self.__dataDirect = "get"

        self.__outputVideoPath = os.path.join(self.__outputPath, "video")
        self.__outputPhotoPath = os.path.join(self.__outputPath, "photo")
        if os.path.exists(self.__outputPath):
            try:
                shutil.rmtree(self.__outputPath)
            except (IOError, OSError, TimeoutError) as e:
                logger.error(f"<Process-Camera> folder: <{self.__outputPath}> could not be deleted for some reason, error message: {repr(e)}")
            else:
                for _ in range(100):
                    if not os.path.exists(self.__outputPath):
                        break
                    time.sleep(1)
        if not os.path.exists(self.__outputVideoPath):
            os.makedirs(self.__outputVideoPath)
        if not os.path.exists(self.__outputPhotoPath):
            os.makedirs(self.__outputPhotoPath)
        logger.debug(f"<Process-Camera> video will be recorded and saved to folder: {self.__outputVideoPath}")
        logger.debug(f"<Process-Camera> photo will be shot and saved to folder: {self.__outputPhotoPath}")

    def run(self):
        # trying to start camera
        logger.info(f"<Process-Camera> start opening camera and getting handler")
        cameraStartStatus = False
        for _ in range(5):
            logger.debug(f"<Process-Camera> trying to open camera")
            self.__cap = cv.VideoCapture(self.__cameraId, cv.CAP_DSHOW)
            self.__cap.set(cv.CAP_PROP_FRAME_WIDTH, self.__resolution[0])
            self.__cap.set(cv.CAP_PROP_FRAME_HEIGHT, self.__resolution[1])
            self.write_setting(self.__cameraSet)
            self.read_settings()
            openStatus = self.__cap.isOpened()
            frameExistsCount = 0
            logger.debug(f"<Process-Camera> camera status is: <{openStatus}>, video size has been set to {self.__cap.get(cv.CAP_PROP_FRAME_WIDTH)} x {self.__cap.get(cv.CAP_PROP_FRAME_HEIGHT)}")
            while openStatus:
                ret, frame = self.__cap.read()
                if ret and frame is not None and isinstance(frame, np.ndarray):
                    cameraStartStatus = True
                    break
                else:
                    logger.error(f"<Process-Camera> can not read frame from camera, return value: ret={ret}, frame size={len(frame) if isinstance(frame, np.ndarray) else 'None'}")
                    frameExistsCount += 1
                    if frameExistsCount >= 60:
                        self.__cap.release()
                        break
                openStatus = self.__cap.isOpened()
            if cameraStartStatus:
                break
        else:
            self.close()
            logger.error(f"<Process-Camera> failed to start camera")
            raise RuntimeError(f"<Process-Camera> failed to start camera")

        size = (int(self.__cap.get(cv.CAP_PROP_FRAME_WIDTH)), int(self.__cap.get(cv.CAP_PROP_FRAME_HEIGHT)))
        # camera connected and opened
        frame_count = 0
        frame_count_per_sec = 0
        # frame_count_per_sec_fps = 0
        # frame_start_t_fps = time.time()
        frame_start_t = time.time()
        logger.info(f"<Process-Camera> camera is ready, starting main loop")
        while True:
            try:
                ret, frame = self.__cap.read()

                # if time.time() - frame_start_t_fps >= 1:
                #     logger.debug(f"fps={frame_count_per_sec_fps}")
                #     frame_start_t_fps = time.time()
                #     frame_count_per_sec_fps = 0
                # frame_count_per_sec_fps += 1

                # communicate with main process
                if self.listen(frame):
                    break

                # check FPS for video, if frame is writing to video file too fast, drop some frame; else writing video file in full speed
                if time.time() - frame_start_t >= 1:
                    # logger.debug(f"fps for video={frame_count_per_sec}")
                    frame_count_per_sec = 0
                    frame_start_t = time.time()
                if frame_count_per_sec / int(self.__fps) >= time.time() - frame_start_t:
                    continue
                frame_count_per_sec += 1
                frame_count += 1

                if frame_count % (int(self.__fps) * 60 * 2) == 0:
                    logger.debug(
                        f"<Process-Camera> <{frame_count}({int(frame_count / 60 / int(self.__fps))}min)> frames retrieved from camera and write to video")

                # add a timestamp to new copied frame
                N = datetime.datetime.now()
                cv.putText(
                    img=frame,
                    text=f"{N.month}-{N.day}_{N.hour}-{N.minute}-{N.second}-{N.microsecond}",
                    org=(10, size[1] - 20),
                    fontFace=cv.FONT_HERSHEY_PLAIN,
                    fontScale=1.0,
                    color=(0, 255, 0),
                    thickness=2
                )
                if self.__videoWriterObj:
                    self.__videoWriterObj.write(frame)
                    if frame_count >= self.__videoSplit * 60 * int(self.__fps):
                        logger.debug(f"<Process-Camera> stop video writer and save video file, <{frame_count}({int(frame_count / 60 / int(self.__fps))}min)> frames saved")
                        self.stop_record()
                        frame_count = 0
                else:
                    # create a new video file and create a file handler for this video file
                    logger.debug(f"<Process-Camera> create a new video writer")
                    self.start_record()
            except Exception as e:
                logger.error(f"<Process-Camera> some other error occurs, error message: {repr(e)}")

    def listen(self, frame):
        """
        listen to main process and react to some commands
        @param:
            frame: frame
        @return:
            bool: False: continue current process, True: stop and exit current process
        @code:
            1000: successfully stopping and exiting camera process
            1001: successfully taking a picture and saved
            1002: successfully reading camera settings and returned
            1003: successfully setting camera settings
            10031: failed setting camera settings because property name is not available
            10032: failed setting camera settings because property value is incorrect
            10033: failed settings camera settings because parameter is not a dict
        """
        exit_flag = False
        # communicate with main process
        try:
            cmd = self.__queueR.get_nowait()
        except (queue.Empty,) as e:
            pass
        else:
            # read command from queue
            if isinstance(cmd, dict) and isinstance(cmd.get("cmd"), int):
                # command for taking picture
                cmd_num = cmd.get("cmd")
                logger.debug(f"cmd={cmd}")
                if cmd_num == 1:
                    pic_path = self.shot(frame)
                    try:
                        self.__queueW.put_nowait({"ret": 1001, "result": pic_path})
                    except (queue.Full,) as e:
                        pass
                # command for exiting sub-process
                elif cmd_num <= 0:
                    self.stop_record()
                    self.close()
                    try:
                        self.__queueW.put_nowait({"ret": 1000})
                    except (queue.Full,) as e:
                        pass
                    exit_flag = True
                # command for reading camera settings
                elif cmd_num == 2:
                    settings = self.read_settings()
                    try:
                        self.__queueW.put_nowait({"ret": 1002, "result": settings})
                    except (queue.Full,) as e:
                        pass
                # command for writing camera settings
                elif cmd_num == 3:
                    data = cmd.get("data")
                    code = 1003
                    if isinstance(data, dict):
                        ret = self.write_setting(data)
                        if ret != 0:
                            code = 10030 + ret
                    else:
                        code = 10033
                    try:
                        self.__queueW.put_nowait({"ret": code})
                    except (queue.Full,) as e:
                        pass
                else:
                    pass
        return exit_flag

    def shot(self, frame, path: str = None):
        """
        take a picture and save it, supported type is (.png)
        @param:
            frame: one frame from camera
            path: the absolute path of the picture
        @return:
            str, the absolute path of picture file
        """
        now = datetime.datetime.now()
        pic_name = f"pic_{now.year}_{now.month}_{now.day}-{now.hour}_{now.minute}_{now.second}_{now.microsecond}.png"
        if not path:
            pic_name = os.path.join(self.__outputPhotoPath, pic_name)
        else:
            pic_name = path
        if not pic_name.endswith(".png") and not pic_name.endswith(".jpg") and not pic_name.endswith(".bmp"):
            pic_name = pic_name + ".png"
        logger.debug(f"take a picture and save as: {pic_name}")
        cv.imencode('.png', frame)[1].tofile(pic_name)
        return pic_name

    def start_record(self):
        """
        generate video file path and create video container object
        """
        now = datetime.datetime.now()
        name = f"record_{now.year}_{now.month}_{now.day}-{now.hour}_{now.minute}_{now.second}.avi"
        videoPath = os.path.join(self.__outputVideoPath, name)
        fourcc = cv.VideoWriter_fourcc(*'XVID')
        size = (int(self.__cap.get(cv.CAP_PROP_FRAME_WIDTH)), int(self.__cap.get(cv.CAP_PROP_FRAME_HEIGHT)))
        logger.info(f"<Process-Camera> start to write frames into video container with size: {size} and path: {videoPath}")
        self.__videoWriterObj = cv.VideoWriter(videoPath, fourcc, self.__fps, size)

    def stop_record(self):
        """
        stop video record and save video
        """
        logger.info(f"<Process-Camera> video record stopped")
        try:
            self.__videoWriterObj.release()
        except (AttributeError, ):
            pass
        self.__videoWriterObj = None

    def close(self):
        """
        stop recording if it's recording and stop child thread and release camera, call this method if you don't want to
        use camera any more
        """
        logger.info(f"<Process-Camera> stop camera and thread")
        # self._record_stop()
        self.__cap.release()

    def write_setting(self, kwargs: dict = None):
        """
        write camera properties, see SETTINGS
        frequently used settings:
            CAP_PROP_BRIGHTNESS [0, 100]
            CAP_PROP_CONTRAST [0, 100]
            CAP_PROP_GAIN [-1, 100]
            CAP_PROP_EXPOSURE [-10, 10]
            CAP_PROP_SHARPNESS [0, 7]
        @param:
            kwargs: "CAP_PROP_POS_MSEC", "CAP_PROP_POS_FRAMES" and etc, no "cv." as prefix
        @return:
            int: 0 : success, others: fail
        """
        ret = 0
        if kwargs:
            for prop_name, prop_value in kwargs.items():
                if str(prop_name).upper() in [x[3:] for x in SETTINGS]:
                    if isinstance(prop_value, str):
                        try:
                            prop_value = float(prop_value)
                        except (AttributeError, TypeError) as e:
                            ret = 2
                            logger.error(f"<Process-Camera> can not set property: {prop_name} = {prop_value} because of value error: {e}")
                            continue
                    self.__cap.set(eval(f"cv.{str(prop_name).upper()}"), prop_value)
                else:
                    ret = 1
                    logger.error(f"<Process-Camera> can not set property: {prop_name}= {prop_value}, available property names are: {[x[3:] for x in SETTINGS]}")
        return ret

    def read_settings(self):
        """
        read all possible camera properties, see SETTINGS
        """
        ret_value = {}
        logger.debug(f"<Process-Camera> reading camera properties:")
        for item in SETTINGS:
            prop_val = self.__cap.get(eval(item))
            logger.debug(f"<Process-Camera> camera property: {item} = {prop_val}")
            ret_value[item[3:]] = prop_val

        return ret_value


if __name__ == "__main__":
    QR = multiprocessing.Queue(1)
    QW = multiprocessing.Queue(1)
    mp = CameraProcess(outputPath=r"D:\Bruce\003_GIT\cluster\ACT\output\camera", queueR=QR, queueW=QW, resolution=(1920, 720), fps=20)
    mp.start()

    time.sleep(60*60*10)
    # import random
    #
    # t1 = time.time()
    # lis = list(range(50000))
    # random.shuffle(lis)
    # tmp = lis[:]
    # selected = []
    # while len(selected) < len(lis):
    #     min_ = tmp[0] if len(tmp) > 0 else 0
    #     ind = 0
    #     for index, item in enumerate(tmp):
    #         if item <= min_:
    #             min_ = item
    #             ind = index
    #     selected.append(min_)
    #     tmp = tmp[:ind] + tmp[ind + 1:]
    #     # print(f"{min_}")

    # print(time.time() - t1)
