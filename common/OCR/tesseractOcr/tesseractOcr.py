#! /usr/bin/env python



"""
home page for tesseract: https://github.com/tesseract-ocr/tesseract
document for tesseract: https://tesseract-ocr.github.io/tessdoc/Home.html
download tesseract installer for windows: https://github.com/UB-Mannheim/tesseract/wiki

we use tesseract5.0 here because 5.0 could be installed directly from an exe file
engine and language data of tesseract5.0 can be found in folder ./engine/Tesseract-OCR

License:
	The code in this repository is licensed under the Apache License, Version 2.0 (the "License");
	you may not use this file except in compliance with the License.
	You may obtain a copy of the License at

	http://www.apache.org/licenses/LICENSE-2.0

	Unless required by applicable law or agreed to in writing, software
	distributed under the License is distributed on an "AS IS" BASIS,
	WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
	See the License for the specific language governing permissions and
	limitations under the License.

examples:
	from common.OCR.tesseractOcr.ocr import Ocr
	Ocr().image_to_string(r"D:/xxx/xxx/xxx.png") -- recognize image using Chinese trained data
	Ocr().image_to_string(r"D:/xxx/xxx/xxx.png", lang=Language.Chinese+Language.English) -- recognize image, main language is Chinese
		and second language is English, used for text with mixed languages(but not good enough)
"""
try:
	from common.logger.logger import logger
except (ImportError, ModuleNotFoundError) as e:
	import logging as logger
from common.OCR.ocr import Ocr
from common.OCR.language import Lang as Language
import subprocess
import cv2 as cv
import time
import os


current_path = os.path.split(os.path.abspath(__file__))[0]
# ENGINE = os.path.join(current_path, "engine", "Tesseract-OCR", "tesseract.exe")
# LANGUAGE_DATA = os.path.join(current_path, "engine", "Tesseract-OCR", "tessdata", "tessdata")


class TesseractOcr(Ocr):
	def __init__(self, tmpFolder: str = None, searchList: (list, tuple) = None):
		"""
		class init
		@param:
			tmpFolder: tmp folder used for storing tmp image
		"""
		self.__tmpFolder = tmpFolder if tmpFolder else os.path.join(os.path.split(os.path.abspath(__file__))[0], "tmp")
		self.languages = [str(x.value) for x in Language._member_map_.values()]
		self.engine, self.language_data = self.__find_engine(searchList)

	def __find_engine(self, searchList: (list, tuple) = None):
		"""
		search root dir of tesseract OCR, and location "tesseract.exe" and language data
		@param:
			searchList: a list of dirs for searching tesseract
		@return:
			tuple: (absolute path of engine, absolute path of language data)
		"""
		engine_dir = None
		language_data_dir = None

		if not searchList:
			searchList = [current_path]
			tmp_path = current_path
			for _ in range(8):
				tmp_path = os.path.split(tmp_path)
				if tmp_path[-1] == '':
					break
				if tmp_path[0] not in searchList:
					searchList.append(tmp_path[0])
				tmp_path = tmp_path[0]

		for p in searchList:
			logger.debug(f"trying to search engine of tesseract OCR('tesseract.exe') from path: <{p}>")
			for root, dirs, files in os.walk(p):
				if "tesseract.exe" in files:
					engine_dir = root
					break
			if engine_dir:
				language_data_dir = os.path.join(engine_dir, "tessdata", "tessdata")
				logger.info(f"language data dir of tesseract OCR found: <{language_data_dir}>")
				engine_dir = os.path.join(engine_dir, "tesseract.exe")
				logger.info(f"engine of tesseract OCR('tesseract.exe') found: <{engine_dir}>")
				break
		else:
			logger.error(f"could not find available engine('tesseract.exe') and language data for tesseract OCR, error"
						f"might occurs if you are trying to use tesseract OCR")

		return engine_dir, language_data_dir

	def image_to_string(self, image, lang: (str, Language) = Language.Chinese + Language.English, **kwargs):
		"""
		use tesseract5.0 as OCR engine
		recognize a image and output string
		@param:
			image: absolute path of input image with characters for recognition or matrix object loaded by opencv
			lang(optional): languages used for recognition, examples: "chi_sim" or "chi_sim+eng"(means recognize with two languages
				and the main language is chi_sim), there's a Enum class which could be used: from automated import Language
			timeout(optional): recognition will stopped if timeout, default to 2s
			tessdata(optional): Specify the location of tessdata path(language's trained data path)
			user_words(optional): Specify the location of user words file
			user_patterns(optional): Specify the location of user patterns file
			dpi(optional): Specify DPI for input image
			psm(optional): Specify page segmentation mode:
						# 0 Orientation and script detection(OSD) only.
						# 1 Automatic page segmentation with OSD.
						# 2 Automatic page segmentation, but no OSD, or OCR.(not implemented)
						# 3 Fully automatic page segmentation, but no OSD.(Default)
						# 4 Assume a single column of text of variable sizes.
						# 5 Assume a single uniform  block of vertically aligned text.
						# 6 Assume a single uniform block of text.
						# 7 Treat the image as a single text line.
						# 8 Treat the image as a single word.
						# 9 Treat the  image as a single word in a circle.
						# 10 Treat the image as a single character.
						# 11 Sparse text.Find as much	text as possible in no	particular	order.
						# 12 Sparse	text with OSD.
						# 13 Raw line.Treat the image as a single text line, bypassing hacks that	are	Tesseract - specific.
			oem(optional): Specify OCR Engine mode, default to 3:
						# 0 Legacy engine only.
						# 1 Neural nets LSTM engine only.
						# 2 Legacy + LSTM engines.
						# 3 Default, based on what is available.
		@return:
			str, result of recognition
		"""
		cmd = [self.engine]
		# check if all languages are available
		if isinstance(lang, Language):
			lang = lang.value
		langList = [x.strip() for x in lang.split("+")]
		for lang_ in langList:
			if lang_ not in self.languages:
				logger.error(f"language type: {lang_} not supported, recognition skipped")
				return None

		tmpPng = None
		if isinstance(image, str) and os.path.exists(image):
			cmd.extend([image, "stdout", "-l", lang])
		else:
			tmpFolder = self.__tmpFolder
			if not os.path.exists(tmpFolder):
				os.makedirs(tmpFolder)
			tmpPng = os.path.join(tmpFolder, f"tmp_{time.time()}.png")
			cv.imwrite(tmpPng, image)
			cmd.extend([tmpPng, "stdout", "-l", lang])

		# terminate the subprocess if timeout
		if "timeout" in kwargs and isinstance(kwargs["timeout"], (int, float)):
			timeout = kwargs["timeout"]
		else:
			timeout = 3

		# Specify the location of tessdata path
		if "tessdata" in kwargs and os.path.exists(kwargs["tessdata"]):
			cmd.extend(["--tessdata-dir", kwargs["tessdata"]])
		else:
			cmd.extend(["--tessdata-dir", self.language_data])
		# Specify the location of user words file
		if "user_words" in kwargs and os.path.exists(kwargs["user_words"]):
			cmd.extend(["--user-words", kwargs["user_words"]])
		# Specify the location of user patterns file
		if "user_patterns" in kwargs and os.path.exists(kwargs["user_patterns"]):
			cmd.extend(["--user-patterns", kwargs["user_patterns"]])
		# Specify DPI for input image
		if "dpi" in kwargs and isinstance(kwargs["dpi"], (int, float)):
			cmd.extend(["--dpi", f'{kwargs["dpi"]}'])
		# Specify page segmentation mode:
		if "psm" in kwargs and isinstance(kwargs["psm"], int) and 0 <= kwargs["psm"] <= 13:
			cmd.extend(["--psm", f'{kwargs["psm"]}'])
		else:
			cmd.extend(["--psm", '6'])
		# Specify OCR Engine mode:
		if "oem" in kwargs and isinstance(kwargs["oem"], int) and 0 <= kwargs["oem"] <= 3:
			cmd.extend(["--oem", f'{kwargs["oem"]}'])
		else:
			cmd.extend(["--oem", '2'])
		logger.debug(f"cmd for tesseract OCR is: <{cmd}>")

		# start a subprocess to call tesseract and stop subprocess after recognition finished or timeout
		try:
			result = subprocess.check_output(cmd, timeout=timeout)
		except (subprocess.TimeoutExpired, ) as e:
			result = None
			logger.warning(f"tesseractOCR can not recognize image and <None> will be returned, error message: {e}")

		if tmpPng and os.path.exists(tmpPng):
			os.remove(tmpPng)

		return result.decode("utf-8").replace(" ", "").replace("\r\n", "")[:-1] if result else None


if __name__ == "__main__":
	test_ocr = r"D:\Bruce\003_GIT\cluster\ACT\resource\image\template\cap_Warning_21.2.24\12V电源系统故障_舒适功能关闭_ocr(1485, 320, 1775, 580).png"
	o = TesseractOcr()
	t1 = time.time()
	res = o.image_to_string(test_ocr)
	print(time.time() - t1)
	print(res)
