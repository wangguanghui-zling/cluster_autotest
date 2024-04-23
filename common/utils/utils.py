#! /usr/bin/env python


try:
	from common.logger.logger import logger
except (ImportError, ModuleNotFoundError) as e:
	import logging as logger
import os
import re
import shutil
import time


class Utils:

	__instance = None

	def __new__(cls, *args, **kwargs):
		if not cls.__instance:
			cls.__instance = super().__new__(cls)
		return cls.__instance

	def __init__(self):
		logger.info(f"initialize utils")

	def clear_test_scripts(self, path: str, clear: bool = True):
		"""
		delete all .py files and parent folders generated from .json files
		@param:
			path: the path to search for .py scripts generated from .json files
			clear: True for perform clear action, False for ignore
		"""
		if not clear:
			logger.warning(f".py files will not be deleted, because <clear={clear}> is not True")
			return
		if not os.path.exists(path):
			logger.error(f"path: <{path}> not exists, can not clear .py scripts")
			return

		delete_list = []
		for root, dirs, files in os.walk(path):
			if str(os.path.split(root)[1]).lower().startswith("test_"):
				scripts_folder = True
				if dirs:
					scripts_folder = False
				else:
					for f in files:
						if not str(f).lower().startswith("test_") or not str(f).lower().endswith(".py"):
							scripts_folder = False
							break
				if scripts_folder:
					delete_list.append(root)
				else:
					for f in files:
						if str(f).lower().startswith("test_") and str(f).lower().endswith(".py"):
							delete_list.append(os.path.join(root, f))

		for df in delete_list:
			if os.path.isdir(df):
				logger.debug(f"deleting folder: <{df}>")
				shutil.rmtree(df, ignore_errors=True)
				for _ in range(30):
					if not os.path.exists(df):
						break
					time.sleep(0.1)
			else:
				logger.debug(f"deleting file: <{df}>")
				os.remove(df)
				time.sleep(0.1)

	def remove_dir(self, dirs: (str, list, tuple)):
		"""
		remove dir and all sub-dirs, used for clearing before test
		@param:
			dirs: the path of dir to remove, default to 'output'
		"""
		if isinstance(dirs, str):
			dirs = [dirs]
		for path in dirs:
			if path and os.path.exists(path):
				shutil.rmtree(path=path, ignore_errors=True)
				for _ in range(50):
					if not os.path.exists(path):
						break
					time.sleep(0.1)

	def create_dir(self, dirs: (str, list, tuple)):
		"""
		create dirs
		@param:
			dirs: one or a serial of dirs
		"""
		if isinstance(dirs, str):
			dirs = [dirs]
		for d in dirs:
			if not os.path.exists(d):
				logger.debug(f"creating dir: <{d}>")
				os.makedirs(d)

	def template_image(self, name: str, searchList: (list, tuple), match: bool = False):
		"""
		search an image from resource and project and return the absolute path of image
		@param:
			name: the full name or part of the name of the image
			match: True: object must be fully matched in character and case sensitive
					False: fuzzy search
			searchList: a list of dirs used for searching template images
		@return:
			str, the absolute path of image or raise error
		"""
		pat = re.compile(r"(.+?)\(.*")
		for path in searchList:
			if not path:
				logger.error(f"[template] or [resource] or [root] not found in settings.ini, please set path first")
				continue
			for root_, dirs, files in os.walk(path):
				for f in files:
					if match:
						if name.lower() == f.lower():
							return os.path.join(root_, f)
					else:
						res = re.match(pat, f)
						if res and res.group(1).lower() == name.lower():
							return os.path.join(root_, f)
		raise FileNotFoundError(f"image not found, 1. <searchList={searchList}> must be set properly for searching, 2.there's no image found")


if __name__ == "__main__":
	u = Utils()
	res = u.template_image("发动机水温过高报警", ["xxxxx", "ccccc"])
	print(res)
