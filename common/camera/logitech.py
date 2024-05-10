#! /usr/bin/env python



"""
this module provide interfaces to control cameras, mainly used for recording and taking photos
camera will be started as you create an instance and two new threads will be started at the same time, camera need some time
to start up in child thread and different camera has different start time.
you can record a video or take a picture after camera started.
this module is mainly used for Non-industrial camera.
how to use:
    # import the module, you can also use "from common import Camera"
    from common.camera.logitech import Logitech as Camera
    cam = Camera(outputPath="xxxxx")  # init camera, two new child threads will be started to manage the camera, so we can do other things in main thread
    path = cam.shot()  # send a command to child thread to take a picture and picture path will returned
    frame = cam.frame  # get a frame from camera
    cam.close()  # stop video recording and camera thread
"""

import cv2 as cv
import threading
import os
import time
import datetime
import shutil
import copy
import numpy as np

try:
    from common.logger.logger import logger
except (ImportError, ModuleNotFoundError) as e:
    import logging as logger
from common.camera.cameraSetting import SETTINGS


class Logitech:

    __instance = None
    __first_initialize = True

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __init__(
            self,
            outputPath: str,
            camera_id: int = 0,
            resolution: (tuple, list) = (640, 480),
            fps: int = 30,
            kwargs: dict = None
    ):
        """
        init an instance
        @param:
            outputPath: a path used for storing both videos and pictures taken from camera
            camera_id: camera id for a specific camera, if only one camera's available then 0 should be used
            resolution: resolution for camera or display, default to (640, 480)
            fps: frame rate per second, default to 30
            kwargs: "CAP_PROP_POS_MSEC", "CAP_PROP_POS_FRAMES" and etc, no "cv." as prefix, see SETTINGS
        """
        if self.__first_initialize:
            self.__class__.__first_initialize = False
            # check and create tmp dirs to store video and photo captured from camera
            self._resolution = resolution
            # if not outputPath:
            #     outputPath = os.path.join(Config.output, "camera")
            if os.path.exists(outputPath):
                try:
                    shutil.rmtree(outputPath)
                except (IOError, OSError, TimeoutError) as e:
                    logger.warning(f"folder: <{outputPath}> could not be deleted for some reason, error message: {repr(e)}")
                else:
                    for _ in range(100):
                        if not os.path.exists(outputPath):
                            break
                        time.sleep(1)
            self.__videoPth = os.path.join(outputPath, "video")
            self.__photoPath = os.path.join(outputPath, "photo")
            if not os.path.exists(self.__videoPth):
                os.makedirs(self.__videoPth)
            if not os.path.exists(self.__photoPath):
                os.makedirs(self.__photoPath)
            logger.info(f"videos and photos will be saved to: {self.__videoPth} and {self.__photoPath}")

            self.__camera = camera_id
            self._stop_camera = False
            self.__camera_started = False
            self._cap = None
            self.__frame = None
            self.__crThd = None
            self.__rfThd = None
            self.__videoOut = None
            self.__video_time = 60
            self.__lock = threading.Lock()
            self._start_camera_thread(fps=fps, kwargs=kwargs)
        else:
            logger.warning(f"already initialized once")

    @property
    def frame(self):
        return copy.deepcopy(self.__frame)

    def _record_start(self, name: str = None, fps: int = 30):
        """
        start to record a video, a command will be sent to child thread, video name must end with ".avi" if passed in
        @param:
            name: the name for saving the video, could be passed in or automatically use current datetime as the name
            fps: frame rate per second, default to 30
        @return:
            str, the absolute path of video file
        """
        if not name:
            now = datetime.datetime.now()
            name = f"record_{now.year}_{now.month}_{now.day}-{now.hour}_{now.minute}_{now.second}.avi"
        if not name.endswith(".avi"):
            logger.warning(f"video name not supported: {name}, video name should end with '.avi'")
            name = name + ".avi"
        videoPath = os.path.join(self.__videoPth, name)
        if os.path.exists(videoPath):
            os.remove(videoPath)
            for i in range(100):
                if not os.path.exists(videoPath):
                    break
                time.sleep(0.1)
        fourcc = cv.VideoWriter_fourcc(*'XVID')
        if self._cap:
            size = (int(self._cap.get(3)), int(self._cap.get(4)))
        else:
            size = (640, 480)
        logger.info(f"start to write frames into video container with size: {size} and path: {videoPath}")
        self.__videoOut = cv.VideoWriter(videoPath, fourcc, fps, size)
        return videoPath

    def _record_stop(self):
        """
        stop and save the video started by "record_start"
        you can start a new recording after calling this method
        this method will be called automatically if the camera will be released
        """
        logger.info(f"video record stopped")
        try:
            self.__videoOut.release()
        except (AttributeError, ):
            pass
        self.__videoOut = None

    def shot(self, name: str = None):
        """
        take a picture and save it, supported type are (.png, .jpg, .bmp)
        @param:
            name: the name for saving the picture, could be passed in or automatically use current datetime as the name
        @return:
            str, the absolute path of picture file
        """
        buffer = self.__frame
        now = datetime.datetime.now()
        pic_name = f"record_{now.year}_{now.month}_{now.day}-{now.hour}_{now.minute}_{now.second}_{now.microsecond}.png"
        if not name:
            picPath = os.path.join(self.__photoPath, pic_name)
        elif name and os.path.isdir(name):
            picPath = os.path.join(name, pic_name)
        elif name and os.path.isfile(name):
            picPath = name
        if not picPath.endswith(".png") and not picPath.endswith(".jpg") and not picPath.endswith(".bmp"):
            picPath = picPath + ".png"
        if os.path.exists(picPath):
            os.remove(picPath)
            for i in range(20):
                if not os.path.exists(picPath):
                    break
                time.sleep(0.1)
        logger.debug(f"take a picture and save it as: {picPath}")
        cv.imwrite(picPath, buffer)
        # cv.imencode('.png', buffer)[1].tofile(picPath)
        return picPath

    def close(self):
        """
        stop recording if it's recording and stop child thread and release camera, call this method if you don't want to
        use camera any more
        """
        logger.info(f"stop camera and thread")
        self._stop_camera = True
        self._record_stop()
        self._cap.release()

    def _start_camera_thread(self, camera_id: int = -1, fps: int = 30, kwargs: dict = None):
        """
        start two new threads as a daemon and open camera in child thread, usually you don't need to call this method
        @param:
            camera_id: camera id, the newest camera will be chosen automatically, you can also passed in an id to choose a
                specific camera if there are more than one
            fps: frame rate per second, default to 30
            kwargs: "CAP_PROP_POS_MSEC", "CAP_PROP_POS_FRAMES" and etc, no "cv." as prefix, see SETTINGS
        """
        if camera_id < 0:
            camera_id = self.__camera
        logger.info(f"start camera threads")
        self.__rfThd = threading.Thread(target=self.__retrieve_frame, args=(camera_id, fps, kwargs), name="Thread-Retrieve")
        self.__rfThd.setDaemon(True)
        self.__rfThd.start()

    def __retrieve_frame(self, camera_id: int, fps: int = 30, kwargs: dict = None):
        """
        retrieve frame from camera
        @param:
            camera_id: camera id, the newest camera will be chosen automatically, you can also passed in an id to choose a
                specific camera if there are more than one
            fps: frame rate per second, default to 30
            kwargs: "CAP_PROP_POS_MSEC", "CAP_PROP_POS_FRAMES" and etc, no "cv." as prefix, see SETTINGS
        """
        # trying to connect camera
        logger.info(f"<Thread-Retrieve> start to open camera and get handler")
        self.__camera_started = False
        for _ in range(10):
            logger.debug(f"<Thread-Retrieve> trying to open camera")
            self._cap = cv.VideoCapture(camera_id, cv.CAP_DSHOW)
            self._cap.set(cv.CAP_PROP_FRAME_WIDTH, self._resolution[0])
            self._cap.set(cv.CAP_PROP_FRAME_HEIGHT, self._resolution[1])
            self.write_settings(kwargs)
            self.read_settings()
            opened = self._cap.isOpened()
            logger.debug(f"<Thread-Retrieve> camera status is: <{opened}>, video size has been set to {self._cap.get(cv.CAP_PROP_FRAME_WIDTH)} x {self._cap.get(cv.CAP_PROP_FRAME_HEIGHT)}")
            no_frame_cnt = 0
            while not self._stop_camera and opened:
                ret, frame = self._cap.read()
                if ret:
                    self.__frame = frame
                    self.__camera_started = True
                    break
                else:
                    logger.error(f"<Thread-Retrieve> can not read frame from camera, return value: ret={ret}, frame size={len(frame) if isinstance(frame, np.ndarray) else 'None'}")
                    no_frame_cnt += 1
                    if no_frame_cnt >= 60:
                        self._cap.release()
                        break
            # cv.imshow("frame", frame)
            # cv.waitKey(1)
            if self.__camera_started:
                break
        else:
            self.close()
            raise RuntimeError(f"<Thread-Retrieve> failed to start camera")

        # black_frame = np.zeros([int(self._cap.get(cv.CAP_PROP_FRAME_HEIGHT)), int(self._cap.get(cv.CAP_PROP_FRAME_WIDTH)), 3], np.uint8)
        size = (int(self._cap.get(cv.CAP_PROP_FRAME_WIDTH)), int(self._cap.get(cv.CAP_PROP_FRAME_HEIGHT)))
        # camera connected and opened
        frame_count = 0
        frame_count_per_sec = 0
        frame_start_t = time.time()
        logger.info(f"<Thread-Retrieve> camera is ready, starting main loop")
        while not self._stop_camera and self.__camera_started:
            try:
                # retrieve one frame from camera
                self.__lock.acquire()
                ret, frame = self._cap.read()
                self.__frame = frame
                self.__lock.release()

                # cv.imshow("1", frame)
                # cv.waitKey(1)

                # check FPS for video, if frame is writing to video file too fast, drop some frame; else writing video file in full speed
                if time.time() - frame_start_t >= 1:
                    frame_count_per_sec = 0
                    frame_start_t = time.time()
                if frame_count_per_sec / int(fps) >= time.time() - frame_start_t:
                    continue
                frame_count_per_sec += 1
                frame_count += 1

                if frame_count % (int(fps) * 60 * 2) == 0:
                    logger.debug(f"<Thread-Retrieve> <{frame_count}({int(frame_count / 60 / int(fps))}min)> frames retrieved from camera and write to video, thread status=<{self.__rfThd.is_alive()}>")

                # add a timestamp to new copied frame
                new_frame = self.__frame
                N = datetime.datetime.now()
                cv.putText(
                    new_frame,
                    f"{N.month}-{N.day}_{N.hour}-{N.minute}-{N.second}-{N.microsecond}",
                    (10, size[1] - 20),
                    cv.FONT_HERSHEY_PLAIN,
                    1.0,
                    (255, 255, 255),
                    1
                )
                if self.__videoOut:
                    self.__videoOut.write(new_frame)
                    if frame_count >= self.__video_time * 60 * int(fps):
                        logger.debug(f"<Thread-Retrieve> terminate video writer and save video file, <{frame_count}({int(frame_count / 60 / int(fps))}min)> frames saved, threading status=<{self.__rfThd.is_alive()}>")
                        self._record_stop()
                        frame_count = 0
                else:
                    # create a new video file and create a file handler for this video file
                    logger.debug(f"<Thread-Retrieve> create a new video writer, threading status=<{self.__rfThd.is_alive()}>")
                    self._record_start(fps=fps)
            except Exception as e:
                logger.error(f"<Thread-Retrieve> some other error occurs, error message: {repr(e)}")

        logger.info(f"<Thread-Retrieve> thread for Retrieving frames from camera stopped")

    def write_settings(self, kwargs: dict = None):
        """
        write camera properties, see SETTINGS
        @param:
            kwargs: "CAP_PROP_POS_MSEC", "CAP_PROP_POS_FRAMES" and etc, no "cv." as prefix
        @return:
            None
        """
        if kwargs:
            for prop_name, prop_value in kwargs.items():
                if str(prop_name).upper() in [x[3:] for x in SETTINGS]:
                    if isinstance(prop_value, str):
                        try:
                            prop_value = float(prop_value)
                        except (AttributeError, TypeError):
                            logger.error(f"can not set property: {prop_name} = {prop_value}")
                            continue
                    self._cap.set(eval(f"cv.{str(prop_name).upper()}"), prop_value)
                else:
                    logger.error(f"can not set property: {prop_name} = {prop_value}, available property name are: {[x[3:] for x in SETTINGS]}")

    def read_settings(self):
        """
        read all possible camera properties, see SETTINGS
        """
        ret_value = {}
        logger.debug(f"camera properties:")
        for item in SETTINGS:
            prop_val = self._cap.get(eval(item))
            logger.debug(f"camera property: {item} = {prop_val}")
            ret_value[item[3:]] = prop_val

        return ret_value


# test
if __name__ == "__main__":
    # kw = None
    # kw = {
    #     "CAP_PROP_BRIGHTNESS": 0,
    #     "CAP_PROP_CONTRAST": 1,
    #     "CAP_PROP_GAIN": -1,
    #     "CAP_PROP_EXPOSURE": -3,
    #     "CAP_PROP_SHARPNESS": 7,  # 0 - 7
    # }
    # cam = Logitech(camera_id=0, resolution=(1920, 1080), outputPath=os.path.join(os.path.split(os.path.abspath(__file__))[0], "tmp"))
    cam = Logitech(camera_id=0, resolution=(1920, 1080),
                   outputPath=r"E:\output1")
    # time.sleep(30)
    # cam.write_settings({
    #     "CAP_PROP_BRIGHTNESS": 40,
    #     "CAP_PROP_CONTRAST": 80,
    #     "CAP_PROP_GAIN": 81,
    #     "CAP_PROP_EXPOSURE": -1,
    #     "CAP_PROP_SHARPNESS": 7,  # 0 - 7
    # })
    # cam.record_start()
    # import random
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

    # time.sleep(60 * 60 * 15)
    # logger.info(f"count down: 3")
    # time.sleep(1)
    # logger.info(f"count down: 2")
    # time.sleep(1)
    # logger.info(f"count down: 1")
    time.sleep(3)
    cam.shot()
    # logger.info(f"count down: 3")
    # time.sleep(1)
    # logger.info(f"count down: 2")
    # time.sleep(1)
    # logger.info(f"count down: 1")
    # time.sleep(1)
    # cam.shot()
    cam.close()
    # time.sleep(2)
