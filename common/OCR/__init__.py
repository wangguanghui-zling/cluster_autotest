#! /usr/bin/env python



"""
combine TesseractOcr and BaiduOcr, automatically choose which engine is the best or available one
if recognition language is available for Baidu OCR then choose BaiduOcr first otherwise choose TesseractOcr

example:
	from common import Ocr
	ocr = Ocr()
	res = ocr.image_to_string(r"D:/xxx/xxx/xxx.png")

	or

	from common import image_to_string
	res2 = image_to_string(r"D:/xxx/xxx/xxx.png")
"""

from common.OCR.tesseractOcr.tesseractOcr import TesseractOcr
from common.OCR.baiduOcr.baiduOcr import BaiduOcr
from common.OCR.language import Lang as Language
from common.OCR.language import BaiDuLang as BaiduLanguage
try:
	from common.logger.logger import logger
except (ImportError, ModuleNotFoundError) as e:
	import logging as logger


__all__ = [
	"Ocr",
	"Language",
]


_baiduFirstLang = (
	Language.Chinese,
	Language.English,
	Language.Japanese,
	Language.Korean,
	Language.French,
	Language.Spanish,
	Language.Portuguese,
	Language.German,
	Language.Italian,
	Language.Russian
)


class Ocr:
	def __init__(
			self,
			tmpFolder: str = None,
			baiduOcrAccountSearchList: (list, tuple) = None
	):
		"""
		class init
		@param:
			tmpFolder: tmp folder used for storing tmp image
			baiduOcrAccountSearchList: a list of dirs used for searching config file(.json) for baidu OCR accounts
		"""
		logger.info(f"initialize OCR")
		self._insTesseractOcr = TesseractOcr(tmpFolder=tmpFolder)
		self._insBaiduOcr = BaiduOcr(tmpFolder=tmpFolder, searchList=baiduOcrAccountSearchList)

	def image_to_string(self, image, lang: (str, Language) = None, **kwargs):
		"""
		recognize a image and output string, using Baidu OCR cloud engine and TesseractOcr local engine
		@param:
			image: absolute path of input image with characters for recognition or matrix object loaded by opencv
			lang(optional): languages used for recognition, default is Chinese and English, for available languages please
				check module doc above
		@return:
			str, result of recognition
			None, can not recognize because of some error
		"""
		if lang is None:
			lang = Language.Chinese
			logger.info(f"OCR language has been set: {lang.value}")
		else:
			logger.info(f"image type: {type(image)}, language type: {type(lang)}, language: {lang}")
		if isinstance(lang, str) and "+" in lang:
			logger.debug(f"more than one language<{lang}> has been set, will call tesseract OCR")
			return self._insTesseractOcr.image_to_string(image, lang, **kwargs)
		elif isinstance(lang, str) and lang.upper() in [str(x.value) for x in BaiduLanguage._member_map_.values()]:
			logger.debug(f"Baidu OCR support language<{lang}>, will call Baidu OCR")
			baiduOcrResult = self._insBaiduOcr.image_to_string(image, lang, **kwargs)
		elif isinstance(lang, str) and lang.lower() in [str(x.value) for x in Language._member_map_.values()]:
			logger.debug(f"Tesseract OCR support language<{lang}>, will call Tesseract OCR")
			return self._insTesseractOcr.image_to_string(image, lang, **kwargs)
		elif isinstance(lang, Language) and lang in _baiduFirstLang:
			tmp_lang = getattr(BaiduLanguage, lang.name).value
			logger.debug(f"language<{tmp_lang}> set is available in both Baidu and Tesseract, try Baidu OCR first")
			baiduOcrResult = self._insBaiduOcr.image_to_string(image, tmp_lang, **kwargs)
		else:
			tmp_lang = lang.value if isinstance(lang, Language) else lang
			logger.debug(f"try Tesseract OCR with language<{tmp_lang}>")
			return self._insTesseractOcr.image_to_string(image, tmp_lang, **kwargs)
		if baiduOcrResult:
			logger.debug(f"Baidu OCR is available, return result")
			return baiduOcrResult
		else:
			lang = lang.value if isinstance(lang, Language) else lang
			logger.debug(f"Baidu OCR return nothing, try Tesseract for further recognize with language<{lang}>")
			return self._insTesseractOcr.image_to_string(image, lang, **kwargs)
