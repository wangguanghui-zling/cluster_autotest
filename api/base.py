#! /usr/bin/env python



from common import logger
from common import CANOE
from common import VehicleConfig
from common import Image
from common import Ocr
from common import Utils
from common import Camera
from common import PowerSupply
from common import Config
from common import DLT
from common import DBC
import time
import numpy
import os


class Base:

    __instance = None
    __first_initialize = True
    Coordinate = None

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __init__(self):
        if self.__first_initialize:
            self.__class__.__first_initialize = False
            logger.info(f"initialize all modules: <camera, dbc, can, image, ocr, dlt, ...>")
            self.config = Config()
            self.cam = Camera(
                outputPath=os.path.join(self.config.output, "camera"),
                resolution=self.config.display
            )
            self.dbc = DBC(
                file=self.config.dbc,
                searchList=[self.config.config]
            )
            self.can = CANOE(
                driver=self.config.driver,
                channel=self.config.canoe_channel,
                cfgFileOe=self.config.cfg_canoe,
                cfgFileLyzer=self.config.cfg_canalyzer
            )
            self.vc = VehicleConfig(
                file="vehicle_config.json",
                searchList=[self.config.config, self.config.root],
                vehicleConfigSourceFile=self.config.vehicle_config,
                vehicleConfigDest=os.path.join(self.config.config, "vehicle_config")
            )

            self.img = Image(
                train_data_path=os.path.join(self.config.resource, "train"),
                model_path=self.config.config
            )
            self.ps = PowerSupply(
                type_=self.config.power,
                port=self.config.power_port
            )

            self.utils = Utils()
            self.ocr = Ocr(
                tmpFolder=os.path.join(self.config.output, "tmp"),
                baiduOcrAccountSearchList=[self.config.config]
            )
            self.image_to_string = self.ocr.image_to_string

            self.dlt = DLT(
                path=self.config.output,
                host=self.config.host,
                port=self.config.port
            )
        else:
            logger.warning(f"all modules have been initialized once")

    def check_cluster(self, status: str = "start"):
        """
        check if cluster has started/restarted successfully or not
        @param:
            status: "start" or "restart"
        @return:
            bool: True for start successfully, False for failed to start
        """
        frame_count = 10
        frame_buffer = []
        boot = False

        blocks = self.config.blocks
        if not blocks or len(blocks) != 2:
            logger.error(f"error config in 'settings.ini': <blocks={blocks}>")
            return False
        display = self.config.display
        if not display or len(display) != 2:
            logger.error(f"error config in 'settings.ini': <display={display}>")
            return False
        brightness_ratio = self.config.brightness_ratio
        if not brightness_ratio or not isinstance(brightness_ratio, float) or brightness_ratio <= 0 or brightness_ratio >= 1:
            logger.warning(f"error config in 'settings.ini': <brightness_ratio={brightness_ratio}>, brightness_ratio will"
                           f"be set to 0.5")
            brightness_ratio = 0.5
        brightness_ratio = 1 - brightness_ratio

        for _ in range(300):
            if isinstance(self.cam.frame, numpy.ndarray):
                logger.info(f"camera started and ready for detecting display status")
                break
            time.sleep(0.1)
        else:
            logger.error(f"can not get frame from camera")
            return False

        logger.info(f"checking display status, blocks={blocks}, display={display}, please wait...")
        start_time = time.time()
        for index in range(1200):
            img_buffer = self.cam.frame
            try:
                bs = self.img.brightness(img_buffer, blocks, display)
            except (AttributeError,) as e:
                logger.debug(f"can not get brightness from screenshot: {e}")
                continue

            bss = [int(x[1]) for x in bs]
            bss = bss[1:]

            # if index % 2 == 0:
            #     logger.debug(f"index={index}, boot={boot}, count={bss.count(0)}, bs={bss}")
            if boot:
                if bss.count(0) / len(bss) > brightness_ratio:
                    frame_buffer.clear()
                    continue
                if len(frame_buffer) >= frame_count:
                    var = []
                    for i in range(len(bss)):
                        tmp = [x[i] for x in frame_buffer]
                        tmp_var = numpy.var(tmp)
                        var.append(tmp_var)
                    # if index % 2 == 0:
                    #     logger.debug(f"var={var}")
                    if len([x for x in var if x < 1]) / len(var) >= 0.9:
                        logger.info(f"display should started, time used: <{round(time.time() - start_time, 3)}>")
                        return True
                    frame_buffer.pop(0)
                else:
                    frame_buffer.append(bss)
            else:
                if status.lower() == "start" and bss.count(0) / len(bss) < brightness_ratio:
                    logger.info(f"display is booting or display has already on")
                    boot = True
                elif status.lower() == "restart" and bss.count(0) / len(bss) > 0.98:
                    logger.info(f"display has already off, start detecting reboot")
                    boot = True
                    start_time = time.time()
            time.sleep(0.1)
        logger.error(f"checking display status timeout")
        raise TimeoutError(f"checking display status timeout")

    def get_message(
            self,
            msgId: (int, str) = None,
            msgName: str = None,
            sigName: str = None,
            sigData: (str, int) = None
    ):
        """
        retrieve specific message frame and signal data, use this method in automated cluster test framework instead of using
            method in DBC module
        @param:
            msgId: message id, used for searching message frame
            msgName: message name, used for searching message frame
            sigName: signal name, used for searching a specific signal from message
            sigData: the signal data to be sent
        @return:
            dict: a dict for message
        """
        items = {
            "msgId":            "message_id",
            "msgName":          "message_name",
            "nodeName":         "node_name",
            "sigName":          "signal_name",
            "sigData":          "",
            "msgSize":          "message_size",
            "sigRawStartBit":   "raw_start_bit",
            "sigStartBit":      "start_bit",
            "sigSize":          "signal_size",
            "sigByteOrder":     "byte_order",
            "sigValueType":     "value_type",
            "sigFactor":        "factor",
            "sigOffset":        "offset",
            "sigMin":           "min_value",
            "sigMax":           "max_value",
            "sigUnit":          "unit",
            "sigReceiver":      "receiver",
            "msgCycleTime":     "cycle_time",
            "msgFrameFormat":   "frame_format",
            "msgSendType":      "send_type",
        }
        data = self.dbc.get_message(msgId=msgId, msgName=msgName, sigName=sigName)
        for key_, value in items.items():
            if value in data:
                items[key_] = data[value]
            else:
                items[key_] = None

        if sigData:
            items["sigData"] = sigData

        return items

    def close(self):
        self.can.close()
        self.cam.close()
        self.ps.disconnect()
        self.dlt.dlt.quit()

    @staticmethod
    def wait(t: int):
        """
        wait 't' ms
        @param:
            t: time to wait, ms
        """
        logger.debug(f"wait for <{t}ms>...")
        time.sleep(t / 1000)

    def find_display(self, refresh: bool = False):
        """
        find coordinates of top-left corner and bottom-right corner of display from camera vision
        @param:
            refresh: force refresh the coordinates
        @return:
            tuple: for integers as a tuple
        """
        if self.__class__.Coordinate is None:
            refresh = True
        if not refresh:
            logger.debug(f"coordinates for display have been found and saved: {self.__class__.Coordinate}")
            return self.__class__.Coordinate

        brightness = self.config.CAP_PROP_BRIGHTNESS
        contrast = self.config.CAP_PROP_CONTRAST
        gain = self.config.CAP_PROP_GAIN
        exposure = self.config.CAP_PROP_EXPOSURE
        sharpness = self.config.CAP_PROP_SHARPNESS

        self.cam.write_settings({
            "CAP_PROP_BRIGHTNESS": brightness[0],
            "CAP_PROP_CONTRAST": contrast[0],
            "CAP_PROP_GAIN": gain[0],
            "CAP_PROP_EXPOSURE": exposure[0],
            "CAP_PROP_SHARPNESS": sharpness[0]
        })
        time.sleep(1)
        sx, sy, ex, ey = self.img.detect_display(self.cam.frame, self.config.display)
        self.cam.write_settings({
            "CAP_PROP_BRIGHTNESS": brightness[1],
            "CAP_PROP_CONTRAST": contrast[1],
            "CAP_PROP_GAIN": gain[1],
            "CAP_PROP_EXPOSURE": exposure[1],
            "CAP_PROP_SHARPNESS": sharpness[1]
        })
        time.sleep(1)
        self.__class__.Coordinate = (sx, sy, ex, ey)

        return sx, sy, ex, ey
