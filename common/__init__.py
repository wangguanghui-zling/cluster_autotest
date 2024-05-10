#! /usr/bin/env python



"""
this file is mainly for the package management of automated test
how to use:
	1. mark the parent directory of "common" as "Sources Root" if you use Pycharm
	2. choose one of following configs if you do not use Pycharm:
		2.1 add code: "sys.path.append(the parent directory's path of 'common')" in .py files in which you want to use common package
		2.2 add or create "the parent directory's path of 'common'" to system environment variable: "PYTHONPATH" or "path"
		2.3 create a new file: "automation.pth" at "Lib/site-packages/" and add a new line: "the parent directory's path of 'common'"
		2.4 you can also put the folder "common" to Python's install path "Lib/site-packages/"

	after you did the config, you can use package as follows:
		from common import logger
		from common import Image

		img = Image()
		logger.info("XXXXXXX")
		img.compare(XXXXX)
"""

from common.logger.logger import logger
from common.image.image import Image
from common.OCR import Language, Ocr
from common.camera import Camera
from common.camera import Camera2
from common.config.config import Config
from common.can import CANoe
# from common.power import PowerSupply
from common.utils.utils import Utils
from common.tc import TestCaseGenerator as TestCaseGenerate
from common.dbc.dbc import DBC
from common.excel import Excel



__all__ = [
	"logger",           # logger module for all other modules
	"Image",            # image comparison
	"Language",         # language Enum for OCR
	"Ocr",              # Ocr
	# "image_to_string",  # Ocr's most useful function and only one for now
	"Camera",           # camera control, a new thread will be started, methods could be called for recording video or taking a picture
	"Camera2",          # camera control, a new sub-process will be started
	"Config",           # load all configs in settings.ini and access configs through this instance
	"CANoe",            # start canoe/canalyzer and provide interface for send/get/swc/vehicle_config
	"Utils",            # some common interfaces such as find a file, remove file and etc.
	"TestCaseGenerate",  # generate test case script
	"DBC",              # DBC parser
	"Excel"            # read and write excel file
]