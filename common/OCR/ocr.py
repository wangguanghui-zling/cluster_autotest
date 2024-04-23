#! /usr/bin/env python



"""
meta class for tesseract OCR and baidu OCR
the goal is to make sure all classes inherit from class Ocr must have specific methods, for uniform interface
this is absolutely necessary for future extension
"""

from abc import ABCMeta, abstractmethod


class Ocr(metaclass=ABCMeta):
	@abstractmethod
	def image_to_string(self, image, lang, **kwargs):
		pass
