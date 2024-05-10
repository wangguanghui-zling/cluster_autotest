#! /usr/bin/env python



"""
main process for camera, communicate with sub-process
"""

import multiprocessing
import time
import queue
import cv2 as cv
import numpy
import os
from common.logger.logger import logger
from common.camera.cameraProcess import CameraProcess
from common.camera.cameraSetting import SETTINGS


class Camera:

    __instance = None
    __first_initialize = True

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __init__(
            self,
            outputPath: str,
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
        init main process of camera
        @param:
            outputPath: a path used for storing both videos and pictures taken from camera
            cameraId: camera id for a specific camera, if only one camera's available then 0 should be used
            resolution: resolution for camera or display, default to (800, 600)
            fps: frame rate per second, default to 20
            videoSplit: split video by time 'videoSplit', default to 60min
            name: name of sub-process
            daemon: set sub-process as a daemon or not, default to True
            cameraSet: "CAP_PROP_POS_MSEC", "CAP_PROP_POS_FRAMES" and etc, no "cv." as prefix, see SETTINGS
            kwargs: some other parameters
        """
        if self.__first_initialize:
            self.__class__.__first_initialize = False
            self.__queueR = multiprocessing.Queue(1)
            self.__queueW = multiprocessing.Queue(1)
            # self.__kwargs = kwargs.copy()
            logger.debug(f"initializing camera process")
            self.__sp = CameraProcess(
                outputPath=outputPath,
                queueR=self.__queueR,
                queueW=self.__queueW,
                cameraId=cameraId,
                resolution=resolution,
                fps=fps,
                videoSplit=videoSplit,
                name=name,
                daemon=daemon,
                cameraSet=cameraSet,
                **kwargs
            )
            logger.debug(f"starting camera process")
            self.__sp.start()
        else:
            logger.warning(f"already initialized once")

    @property
    def frame(self):
        """
        take a picture and open it using opencv
        @return:
            cv.mat: a numpy.ndarray object of image
        """
        path = self.shot()
        if isinstance(path, str) and os.path.exists(path):
            img = cv.imdecode(numpy.fromfile(path, dtype=numpy.uint8), cv.IMREAD_COLOR)
            return img
        return None

    def shot(self, path: str = None):
        """
        take a picture and save it, supported type is (.png)
        @param:
            path: the absolute path of the picture
        @return:
            str, the absolute path of picture file
        """
        t1 = time.time()
        if self._send({"cmd": 1}):
            ret = self._retrieve()
            if ret.get("ret") == 1001:
                logger.info(
                    f'successfully taking one picture from camera within {round(time.time() - t1, 2)}s, and saved as: {ret.get("result")}')
                return ret.get("result")

    def close(self):
        """
        close sub-process
        """
        if self._send({"cmd": 0}):
            ret = self._retrieve()
            if ret.get("ret") == 1000:
                logger.info(f"camera process has been closed")
                return
        logger.error(f"camera process has not been closed properly, please check and kill camera process manually")

    def read_settings(self):
        """
        read all possible camera properties, see cameraSetting
        """
        t1 = time.time()
        if self._send({"cmd": 2}):
            for _ in range(3):
                ret = self._retrieve()
                if ret and ret.get("ret") == 1002:
                    logger.debug(f"successfully reading camera settings within {round(time.time() - t1, 2)}s")
                    return ret.get("result")
        logger.error(f"failed reading camera settings")

    def write_settings(self, kwargs: dict):
        """
        write camera properties, see cameraSetting
        commonly used properties:
            CAP_PROP_BRIGHTNESS [0, 100]
            CAP_PROP_CONTRAST [0, 100]
            CAP_PROP_GAIN [0, 100]
            CAP_PROP_EXPOSURE [-10, 10]
            CAP_PROP_SHARPNESS [0, 7]
        @param:
            kwargs: "CAP_PROP_POS_MSEC", "CAP_PROP_POS_FRAMES" and etc, no "cv." as prefix
        @return:
            None
        """
        t1 = time.time()
        if self._send({"cmd": 3, "data": kwargs}):
            ret = self._retrieve()
            if ret.get("ret") == 1003:
                logger.debug(f"successfully setting camera settings within {round(time.time() - t1, 2)}s")
            elif ret.get("ret") == 10031:
                logger.error(f"failed setting camera settings because property name is not available, available settings are: {SETTINGS}")
            elif ret.get("ret") == 10032:
                logger.error(f"failed setting camera settings because property value is incorrect, must be int or float")
            elif ret.get("ret") == 10033:
                logger.error(f"failed setting camera settings because parameter is not a dict")
            else:
                logger.error(f"failed retrieving camera settings")

    def _send(self, cmd: dict):
        """
        send command to camera process
        @param:
            cmd: command in dict type
        """
        for _ in range(100):
            try:
                self.__queueW.put_nowait(cmd)
            except (queue.Full,) as e:
                pass
            else:
                return True
            time.sleep(0.01)
        logger.error(f"failed sending command to camera process")
        return False

    def _retrieve(self):
        """
        get result from camera process
        @return:
            dict: result of command sending by "_send"
        """
        for _ in range(100):
            try:
                retVal = self.__queueR.get_nowait()
                logger.debug(f"ret={retVal}")
            except (queue.Empty,) as e:
                pass
            else:
                return retVal
            time.sleep(0.01)
        logger.error(f"failed retrieving result from camera process")
        return None


if __name__ == "__main__":
    cam = Camera(outputPath=r"E:\output1", resolution=(1920, 1080), fps=30)
    time.sleep(60*1)
    cam.shot()
    time.sleep(60*1)
    sets = cam.read_settings()
    logger.debug(f"{sets}")
    time.sleep(60*1*1)
    cam.write_settings({
        "CAP_PROP_BRIGHTNESS": 40,
        "CAP_PROP_CONTRAST": 80,
        "CAP_PROP_GAIN": 81,
        "CAP_PROP_EXPOSURE": -1,
        "CAP_PROP_SHARPNESS": 7,  # 0 - 7
    })
    time.sleep(60*1)
