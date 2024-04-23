#! /usr/bin/env python



"""
this module is mainly used for loading configurations from settings.ini and provide a interface to visit all configs
this module is a singleton, so please feel free to import and use this module almost any where
example:
	# settings.ini
		a=1
		b=2

	# your module
	from common.config.config import Config
	print(Config.a) -> 1
	print(Config.b) -> 2
"""

import os
import shutil
import configparser


_current_path = os.path.split(os.path.abspath(__file__))[0]
# define folder names under root, if a folder named "ACT" and has below folders then it will be treated as root
IS_ROOT = ("api", "common", "config", "resource", "test", "tools")


__all__ = [
	"Config"
]


class Config:

	__instance = None
	__first_initialize = True

	def __new__(cls, *args, **kwargs):
		if not cls.__instance:
			cls.__instance = super().__new__(cls, *args, **kwargs)
		return cls.__instance

	def __init__(self):
		if self.__first_initialize:
			self.__class__.__first_initialize = False
			# find the root directory of automated test framework "ACT"
			# find by searching file __init__.py, if exists then it is a package, and the root should not be a package.
			path = os.path.dirname(__file__)
			while os.path.exists(os.path.join(path, '__init__.py')):
				path = os.path.dirname(path)
				subs = os.listdir(path)
				if all(map(lambda x: x in subs, IS_ROOT)):
					break
			self.root = path

			# find config file for test framework
			source_config = os.path.join(_current_path, "settings.ini.bak")
			if not os.path.exists(source_config):
				source_config = self.find_settings("settings.ini.bak")
			_config_path = source_config[:-4]
			if not os.path.exists(_config_path):
				shutil.copyfile(source_config, _config_path)
			# logger.info(f"config file for test framework found: {_config_path}")

			# load config file settings.ini and read all configs
			conf = configparser.ConfigParser(defaults={"ROOT_DIR": self.root})
			conf.read(_config_path, encoding="utf-8")
			# set all configs as attributes of instance
			self.all = {}
			for section in conf.sections():
				for name, value in conf.items(section):
					try:
						value = eval(value)
					except (NameError, TypeError, SyntaxError) as e:
						pass
					finally:
						setattr(self, name, value)
						self.all[name] = value

	def __getattr__(self, item):
		if item in self.__dict__:
			return self.__dict__[item]
		elif item in self.__class__.__dict__:
			return self.__class__.__dict__[item]
		return None

	def find_settings(self, file: str = "settings.ini"):
		"""
		search config file according to file provided
		@param:
			file: search config file according to file provided
		@return:
			str, absolute pah of config file
		"""
		searchPaths = [os.path.join(self.root, "config"), self.root]

		# trying to search a dbc file from project root
		for path in searchPaths:
			for root_, dirs, files in os.walk(path):
				for f in files:
					if f.lower() == file.lower():
						return os.path.join(root_, f)

		raise FileNotFoundError(f"no config file has been detected, please create one first.")


# make sure class Config has been initialized and all configs has been set as attributes
# Config = Config()


if __name__ == "__main__":
	conf = configparser.ConfigParser(defaults={"ROOT_DIR": "aaaa"})
	# conf.read("settings.ini", encoding="utf-8")
	# print(conf.sections())
	# items = conf.items("PATH")
	# print(items)
	print(Config().log_backup_count)
