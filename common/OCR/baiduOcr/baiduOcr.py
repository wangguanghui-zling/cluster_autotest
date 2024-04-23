#! /usr/bin/env python



"""
Baidu OCR: https://console.bce.baidu.com/ai/?_=1609209481393#/ai/ocr/overview/index

this module recognize image using baidu OCR cloud engine through http requests, please find more information from above link

setup:
	1.create one or many accounts in baidu OCR website
	2.create a new(if you don't have one) application for OCR
	3.remember your appID, APIkey and secretKey, it's better to write these info to "account.json"

examples:
	from common.OCR.baiduOcr.baiduOcr import BaiduOcr as Ocr
	Ocr().image_to_string(r"D:/xxx/xxx/xxx.png") -- recognize image with Chinese + English by default
	Ocr().image_to_string(r"D:/xxx/xxx/xxx.png", lang=Language.Japanese.value) -- recognize image with Japanese

support languages:
	Chinese = "CHN_ENG"
	English = "ENG"
	Japanese = "JAP"
	Korean = "KOR"
	French = "FRE"
	Spanish = "SPA"
	Portuguese = "POR"
	German = "GER"
	Italian = "ITA"
	Russian = "RUS"

support file extension:
	jpg/jpeg/png/bmp

recognition times:
	9000 per day for personal authentication(currently in use, but we can register many accounts to enlarge the number, please write new account to account.json)
	49000 per day for company authentication
"""

import json
try:
	from common.logger.logger import logger
except (ImportError, ModuleNotFoundError) as e:
	import logging as logger
from common.OCR.ocr import Ocr
from common.OCR.language import BaiDuLang as Language
# from common.config.config import Config
import os
import requests
import base64
import time
import cv2 as cv


current_path = os.path.split(os.path.abspath(__file__))[0]
request_url = "https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic"
request_url_acc = "https://aip.baidubce.com/rest/2.0/ocr/v1/accurate_basic"


class BaiduOcr(Ocr):
	def __init__(self, tmpFolder: str = None, searchList: (list, tuple) = None):
		"""
		class init
		@param:
			tmpFolder: tmp folder used for storing tmp image
			searchList: a list of dirs used for searching config file(.json) for baidu OCR accounts
		"""
		self.__tmpFolder = tmpFolder if tmpFolder else os.path.join(os.path.split(os.path.abspath(__file__))[0], "tmp")
		self.jsonPath = os.path.join(current_path, "baidu_ocr_accounts.json")
		if not os.path.exists(self.jsonPath):
			self.jsonPath = self.find_ocr_config(searchList=searchList)
		self.account = None

	def access_token(self):
		"""
		load access token and expired time from account.json, if access token expired or not exists, then update it
		@return:
			str, access token requested from baidu OCR cloud engine
			None, no access token available(the times for recognition expired for all users or some other problem)
		"""
		with open(self.jsonPath, 'r') as f:
			self.account = json.load(f)
		for name, item in self.account.items():
			if item["expiresIn"] - time.time() > 0 and item["accessToken"]:
				logger.debug(f"access token for user '{name}' is still available with expires in: {item['expiresIn'] - time.time()} s, directly use this")
				return item["accessToken"]
			else:
				host = f'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={item["APIkey"]}&client_secret={item["secretKey"]}'
				response = requests.get(host)
				if response:
					result = response.json()
					if "access_token" in result and "expires_in" in result:
						self.account[name]["accessToken"] = result["access_token"]
						self.account[name]["expiresIn"] = result["expires_in"] + time.time()
						with open(self.jsonPath, 'w') as f:
							json.dump(self.account, f)
						logger.debug(f"access token for user '{name}' has expired, get new access token from baidu and update json")
						return result["access_token"]
					elif "error" in result and "error_description" in result:
						if result["error"] == "invalid_client" and result["error_description"] == "unknown client id":
							logger.error(f"APIkey for user '{name}' is not correct, please check and correct it")
							continue
						elif result["error"] == "invalid_client" and result["error_description"] == "Client authentication failed":
							logger.error(f"Secret key for user '{name}' is not correct, please check and correct it")
							continue
				else:
					continue
		return None

	def image_to_string(self, image, lang: (str, Language) = None, acc: bool = False, **kwargs):
		"""
		recognize a image and output string, using Baidu OCR cloud engine
		@param:
			image: absolute path of input image with characters for recognition or matrix object loaded by opencv
			lang(optional): languages used for recognition, default is Chinese and English, for available languages please
				check module doc above
			acc(optional): False for normal OCR and True for accurate OCR
		@return:
			str, result of recognition
			None, can not recognize because of some error
		"""
		tmpPng = None
		# read image
		if not isinstance(image, str) or not os.path.exists(image):
			tmpFolder = self.__tmpFolder
			if not os.path.exists(tmpFolder):
				os.makedirs(tmpFolder)
			tmpPng = os.path.join(tmpFolder, f"tmp_{time.time()}.png")
			cv.imwrite(tmpPng, image)
			image = tmpPng
		with open(image, "rb") as f:
			img = base64.b64encode(f.read())

		# prepare params for Baidu OCR http POST request
		if not lang:
			lang = Language.Chinese.value
		elif isinstance(lang, Language):
			lang = lang.value
		param = {"image": img, "language_type": lang}
		access_token = self.access_token()
		if access_token is None:
			logger.error(f"no available access token found from account.json")
			return None
		if acc:
			url = request_url_acc + "?access_token=" + access_token
		else:
			url = request_url + "?access_token=" + access_token
		headers = {'content-type': 'application/x-www-form-urlencoded'}

		# remove tmp image
		if tmpPng and os.path.exists(tmpPng):
			os.remove(tmpPng)

		# send post request and get response for Baidu OCR
		response = None
		for _ in range(3):
			try:
				response = requests.post(url, data=param, headers=headers)
				break
			except (requests.exceptions.SSLError, requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout) as e:
				logger.error(f"Baidu OCR can not perform recognition because of error: {e}")
				response = None
		if response:
			result = response.json()
			if "words_result" in result:
				return "".join([x["words"].replace(" ", "") for x in result["words_result"] if "words" in x])

		return None

	def find_ocr_config(self, searchList: (list, tuple) = None):
		"""
		search config file for baidu ocr: baidu_ocr_accounts.json
		@param:
			searchList: a list of dirs used for searching config file(.json) for baidu OCR accounts
		@return:
			str, absolute pah of config file
		"""
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
		else:
			searchList = list(searchList)
			searchList.append(current_path)

		# trying to search a config file from project root
		for path in searchList:
			if not path:
				logger.error(f"path for [config] or [root] has not been set in settings.ini")
				continue
			for root_, dirs, files in os.walk(path):
				for f in files:
					if f.lower() == "baidu_ocr_accounts.json":
						return os.path.join(root_, f)
					elif f.lower().endswith(".json") and ("baidu_ocr" in f.lower() or "ocr" in f.lower() or "baidu" in f.lower()):
						return os.path.join(root_, f)
		else:
			logger.error(f"no config file has been detected from: {searchList}, please create a config file for baidu OCR first.")
			raise FileNotFoundError(f"no config file has been detected from: {searchList}, please create a config file for baidu OCR first.")


if __name__ == "__main__":
	test_ocr = r"D:\Bruce\003_GIT\ACT\output\images\bg.jpg"
	bdOcr = BaiduOcr()
	t1 = time.time()
	res = bdOcr.image_to_string(test_ocr)
	print(time.time() - t1)
	print(res)
