#! /usr/bin/env python


from api.base import Base
try:
    from common import logger
except (ImportError, ):
    import logging as logger
import os
import re
import time
import allure
import numpy
import threading
import cv2 as cv


class _API(Base):
    def __init__(self):
        super().__init__()
        self._update_vehicle_config()

    def _update_vehicle_config(self):
        logger.info(f"update vehicle config based on CAN project")
        vcs = self.can.vehicle_config_values(*self.vc.names)
        self.vc.update(*vcs)

    def reset_measurement(self):
        reset = self.config.reset_measurement
        if str(reset).lower() == "true":
            self.can.app.stop_Measurement()
            time.sleep(3)
            self.can.app.start_Measurement()
            time.sleep(2)

    def attachment(self, targetImg, tmpImg, name: str = "Image"):
        _mig = self.img.merge(targetImg, tmpImg, targetImg)
        logger.info(f"attach file to allure report: {_mig}")
        allure.attach.file(_mig, name, allure.attachment_type.PNG)

    def set_vehicle_config(self, *pairs):
        logger.info(f"check vehicle config and set")
        pairs = [(name, int(value, 2) if isinstance(value, str) else value) for name, value in pairs]
        update_pairs = self.vc.exists(*pairs)
        if update_pairs:
            success = self.can.vehicle_config(self.check_cluster, *update_pairs)
            if success:
                self.vc.update(*success)

    def button(self, action: str, key_: str):
        logger.info(f"press button(SWC): {action} {key_}")
        self.can.swc(key_, action)

    def send(self, msgId: (str, int), sigName: str, sigData: str):
        """
        send signal or CtlFlag
        @param:
            msgId: str, message id
            sigName: str, signal name
            sigData: str, the data to be sent
        """
        logger.info(f"send can message: msgId={msgId}, sigName={sigName}, sigData={sigData}")
        if sigName.lower() == "ctlflag":
            self.can.ctl_flag(**self.get_message(msgId=msgId, sigName=sigName, sigData=sigData))
        else:
            result = self.can.send(**self.get_message(msgId=msgId, sigName=sigName, sigData=sigData))
            if result == 0:
                self.dbc.store_current_signal_value(msgId, sigName, sigData)

    def reset_signals(self):
        """
        reset signal values
        """
        signals = self.dbc.get_default_signal_values()
        if signals:
            logger.info(f"reset signal values to initial value")
            for sig in signals:
                try:
                    self.can.send(**self.get_message(msgId=sig["msgId"], sigName=sig["sigName"], sigData=sig["sigData"]))
                except (RuntimeError, ) as e:
                    logger.error(f"can not reset signal: <{sig}> because of some errors: {e}")

    def get(self, msgId: (str, int), sigName: str):
        """
        get signal value
        @param:
            msgId: str, message id
            sigName: str, signal name
        """
        return self.can.get(**self.get_message(msgId=msgId, sigName=sigName))

    def battery(self, status: str, check: bool = True):
        """
        perform battery on or off
        @param:
            status: 'on': battery on
                    'off': battery off
            check: True for detect display on, False for no detecting
        """
        logger.info(f"current threading status = <{threading.enumerate()}>")
        sta = self.ps.get_status()
        if not sta:
            logger.error(f"no programmable power supply connected")
            return
        logger.info(f"set battery: {status}")
        if status.lower() == "on":
            if not sta['output on']:
                self.ps.power_on()
                if check:
                    self.check_cluster(status="start")
            else:
                logger.info(f"battery has already on")
        else:
            if sta['output on']:
                self.ps.power_off()
            else:
                logger.info(f"battery has already off")

    # modify by jianglianye 2020-05-19
    def reset_battery(self, voltage: float = 13.5):
        """
        reset voltage to normal and check display status
        """
        # set BAT on,voltage
        # get PowerMod status,if KL15 on, check screen is light;else set KL15 on,then check screen is light
        self.battery('on', check=False)
        time.sleep(1)
        self.ps.set_voltage(voltage)
        # start measurement of CANOE/CANAlyzer if it's off
        self.can.app.start_Measurement()
        # Two cycles to check Power Mod status
        for i in range(2):
            try:
                current_status = int(self.can.get(**self.get_message(msgId="0x295", sigName="SysPowerMod")))
            except RuntimeError as e:
                logger.error(f"Power Mod value is not get,check it status,{e}")
                continue
            if current_status != 2:
                self.kl15(status='on', check=False)
            try:
                self.check_cluster(status='start')
                logger.info('screen is light up')
                return
            except TimeoutError:
                logger.error(f'screen light up time out, it will be BAT reset ')
                self.battery('off')
                time.sleep(1)
                self.battery('on', check=False)
                time.sleep(1)
                self.check_cluster(status='restart')
                return

    def kl15(self, status: str, check: bool = True):
        """
        perform KL15 on or off
        @param:
            status: 'on': KL15 on
                    'off': KL15 off
        """
        logger.info(f"set kl15: {status}")
        current_status = int(self.can.get(**self.get_message(msgId="0x295", sigName="SysPowerMod")))
        if status.lower() == "on":
            if current_status == 2:
                logger.info(f"kl15 is already on")
            else:
                self.can.send(**self.get_message(msgId="0x295", sigName="SysPowerMod", sigData="2"))
                if check:
                    self.check_cluster(status="start")
                time.sleep(3)  # sleep 3 seconds to skip self-checking
        else:
            if current_status == 0:
                logger.info(f"kl15 is already off")
            else:
                self.can.send(**self.get_message(msgId="0x295", sigName="SysPowerMod", sigData="0"))

    def image_compare(
            self,
            templateImgName,
            threshold: float = 90.0,
            timeout: int = 10,
            gray: bool = True,
            iconExists: bool = True,
            **kwargs
    ):
        """
        compare template image with frames from camera and output a serial of similarity rates,
        and decide what to do with similarity rates
        @param:
            templateImg: name of template image
            timeout:  wait icon appear for timeout seconds and return result
            threshold: a threshold for returning, directly return result if similarity is higher than threshold else waiting until timeout
                if threshold is a negative number, wait icon disappear for timeout seconds and return result
            gray(optional): set two images to gray, default to True
            iconExists(optional): check the icon exists if True, else check the icon not exists
        """
        # find template image and location
        template_image = self.utils.template_image(templateImgName, searchList=[self.config.template, self.config.resource])
        location = re.match(r".*?\((\d+),\s*?(\d+),\s*?(\d+),\s*?(\d+)\)", os.path.split(template_image)[1]).groups()
        location = [int(x) for x in location]
        logger.info(f"template image found: path={template_image}, location={location}")
        template_image = cv.imdecode(numpy.fromfile(template_image, dtype=numpy.uint8), cv.IMREAD_COLOR)
        camera_type = str(self.config.camera).lower().strip()

        # read frame from frame queue and compare
        start_t = time.time()
        similarity = 0.0
        target_image = None
        label = None
        nlocation = location[:]
        for index in range(1000):
            if time.time() - start_t < timeout:
                target_image = self.cam.frame
                if camera_type == "lvds":
                    similarity, nlocation = self.img.compare2(
                        target_image,
                        template_image,
                        location=location,
                        threshold=100,
                        gray=gray,
                        mark=0,
                        **kwargs
                    )
                else:
                    target_image = self.img.resize_display(target_image, self.config.display, self.find_display())
                    similarity, label, nlocation = self.img.predict(target_image, template_image, location, factor=4, exists=iconExists)
                logger.info(f"similarity is: {similarity} and location is: {nlocation} and label is: {label}")
                if similarity * 100 >= threshold:
                    logger.info(f"image detected, comparison passed")
                    break
            else:
                logger.error(f"TimeoutError: image: <{templateImgName}> not detected within <{timeout}s>")
                break

        if nlocation:
            target_image = cv.rectangle(target_image, (nlocation[0] - 3, nlocation[1] - 3), (nlocation[2] + 3, nlocation[3] + 3), [0, 255, 255], 1)
        fn = self.img.save(target_image, os.path.join(self.config.output, "camera", "photo"))
        self.attachment(fn, template_image, fn)
        return similarity, nlocation, label

    def ocr_compare(
            self,
            templateImgName,
            ocrExpect: str,
            timeout: int = 10,
            **kwargs
    ):
        """
        get the result of OCR and match with expectation
        @param:
            templateImgName: name of template image
            timeout:  wait text appear for timeout seconds and return result
            ocrExpect: directly return result if text appear else waiting until timeout
        """
        # find template image and location
        template_image = self.utils.template_image(templateImgName, searchList=[self.config.template, self.config.resource])
        location = re.match(r".*?\((\d+),\s*?(\d+),\s*?(\d+),\s*?(\d+)\)", os.path.split(template_image)[1]).groups()
        location = [int(x) for x in location]
        logger.info(f"template image found: path={template_image}, location={location}")
        camera_type = str(self.config.camera).lower().strip()

        # read frame from frame queue and compare
        start_t = time.time()
        nlocation = location[:]
        target_image = None
        result = ''
        for index in range(1000):
            if time.time() - start_t < timeout:
                target_image = self.cam.frame
                if camera_type == "lvds":
                    target_image_ocr = self.img.cut(target_image, *location)
                    result = self.image_to_string(target_image_ocr)
                    logger.info(f"result of OCR: {result}")
                    if result.strip() == ocrExpect.strip():
                        logger.debug(f"characters in image: '{templateImgName}' found, comparison passed")
                        break
                else:
                    target_image = self.img.resize_display(target_image, self.config.display, self.find_display())
                    locs = self.img.object_detect(target_image, location, factor=4)
                    for x1, y1, x2, y2 in locs:
                        result = self.image_to_string(target_image[y1:y2, x1:x2])
                        logger.info(f"result of OCR: {result}")
                        if result.strip() == ocrExpect.strip():
                            logger.debug(f"characters in image: '{templateImgName}' found, comparison passed")
                            nlocation = [x1, y1, x2, y2]
                            break
            else:
                logger.error(f"TimeoutError: characters in image: <{templateImgName}> not detected within <{timeout}s>")
                break

        target_image = cv.rectangle(target_image, (nlocation[0] - 3, nlocation[1] - 3), (nlocation[2] + 3, nlocation[3] + 3), [0, 255, 255], 1)
        fn = self.img.save(target_image, os.path.join(self.config.output, "camera", "photo"))
        self.attachment(fn, template_image, fn)
        return result, nlocation


if __name__ == '__main__':
    api = _API()
    api.image_compare(templateImgName='胎压过低_ocr')
