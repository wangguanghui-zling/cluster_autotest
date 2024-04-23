#! /usr/bin/env python



"""
image.py is used for image comparison and image search, please check method doc for detail or usage
usually used methods are:
	1.compare: used to compare two images with same shape and size or compare selected areas of two images with same shape and size
	2.search: used to search a template image in a bigger target image and return the best match
	3.draw_rect: used to draw rectangles in image, you can passed in one or more than one group of coordinate
	4.cut: used to cut a selected area from a bigger image
	5.similarity: use hanming distance arithmetic to compare the similarity of two images
	6.merge: merge two images into one
	7.blink: detect the blink icons in video

example 1:
	from common import Image

	Image().search(r"D:/xxx/xxx/target.png", r"D:/xxx/xxx/template.png") -> (0.999, (0, 0, 100, 100))
	Image().search(r"D:/xxx/xxx/target.png", r"D:/xxx/xxx/template.png", "template") -> (0.999, (0, 0, 100, 100))
	Image().draw_rect(r"D:/xxx/xxx/target.png", [0, 0, 100, 100], [10, 10, 50, 50])

example 2:
	from common import Image

	Image().compare(r"D:/xxx/xxx/target.png", r"D:/xxx/xxx/template.png", includes=[1, 1, 100, 100]) -> (0.987, (1, 1, 100, 100))

example 3:
	Image().compare(r"D:/xxx/xxx/target.png", r"D:/xxx/xxx/template.png", includes=[[0, 0, 100, 100], [101, 101, 150, 150]])
		-> [(0.987, (0, 0, 100, 100)), (0.789, (101, 101, 150, 150))]

example 4:
	Image().compare(r"D:/xxx/xxx/target.png", r"D:/xxx/xxx/template.png", excludes=[[0, 0, 100, 100], [101, 101, 150, 150]])
		-> (0.99999, (0, 0, 1920, 720))

example 5:
	Image().compare(r"D:/xxx/xxx/target.png", r"D:/xxx/xxx/template.png") -> (0.99999, (0, 0, 1920, 720))

example 6:
	Image().similarity(r"D:/xxx/xxx/target.png", r"D:/xxx/xxx/template.png") -> 0.888

example 7:
	Image().blink(r"D:/xxx/xxx.avi", r"D:/xxx/on.png", r"D:/xxx/off.png", location=(10, 10, 60, 60)) -> (True, 2, 1.5)

example 8: remove background and compare
	Image().compare(r"D:/xxx/xxx.png", r"D:/xxx/xxxx.png", filter=True, threshold=128) -> (0.978, (0, 0, 324, 325))

please check the corresponding method for detail information
"""
try:
	from common.logger.logger import logger
except (ImportError, ModuleNotFoundError) as e:
	import logging as logger
import cv2 as cv
import numpy
import os
import copy
import datetime
from common.image.process import ImageProcessing
from common.image.tensor import Tensor


class Image(ImageProcessing):
	def __init__(
			self,
			train_data_path: str = None,
			model_path: str = None,
			project: str = None,
			train_pct: float = 90,
			model_name: str = "model.h5"
	):
		"""
		init Image engines
		@param:
			train_data_path: absolute path of image data, tensorflow only
			model_path: absolute path of trained model, tensorflow only
			project(optional): project name, B02, B03, P05, etc, tensorflow only
			train_pct(optional): percent for train image, tensorflow only
			model_name(optional): model name, tensorflow only
		"""
		super().__init__()
		if train_data_path and os.path.exists(train_data_path):
			self.__tf = Tensor(train_data_path, model_path, project, train_pct, model_name)
		else:
			logger.warning(f"'train_data_path' must be set before initializing tensorflow engine")
			self.__tf = None
		self.templateMethods = [cv.TM_SQDIFF_NORMED, cv.TM_CCORR_NORMED, cv.TM_CCOEFF_NORMED]

	def compare2(self, targetImg, tmpImg, gray: bool = True, **kwargs):
		"""
		compare two images using feature detect and some other algorithms, not pixel by pixel
		@param:
			targetImg: absolute path of target image or matrix object of image, must be in same shape and size with tmpImg
			tmpImg: absolute path of template image or matrix object of image, must be in same shape and size with targetImg
			gray(optional): set two images to gray, default to True
			**kwargs:
				location(optional): four integers as a list to cut a rectangle area from targetImg, and compare with tmpImg
				other available parameters: see self.compare() for detail
		@return:
			tuple: (float: similarity, tuple: location)
		"""
		if "mark" in kwargs and isinstance(kwargs["mark"], int):
			mark = kwargs["mark"]
			if mark < 0 or mark > 3:
				mark = 1
		else:
			mark = 1

		targetImage, templateImage = self._load(targetImg, tmpImg, True)
		if "location" in kwargs and isinstance(kwargs["location"], (list, tuple)) and len(kwargs["location"]) == 4:
			location = [int(x) for x in kwargs["location"]]
			targetImage = self.cut(targetImage, *location)
			kwargs.pop('location')
		else:
			location = [-1, -1, -1, -1]
			mark = 0

		result0 = 0
		nlocation = location[:]
		minGray, maxGray = numpy.min(templateImage), numpy.max(templateImage)
		if maxGray - minGray > 50:
			result0, label, ntlocation = self.predict(targetImg, tmpImg, location=location, factor=4)

		result1 = self.feature_match(targetImage, templateImage)
		result2, loc = self.compare(targetImage, templateImage, gray=True, **kwargs)
		result3 = self.structure_similarity(targetImage, templateImage)
		result4 = self.template_math(targetImage, templateImage)
		logger.debug(f"calling methods which compare two images pixel by pixel and result is : <{result2}, {location}>")
		ret = max([result0, result1, result2]), nlocation
		targetImageColor, templateImageColor = self._load(targetImg, tmpImg, False)
		if not gray and not self.colored_match(targetImageColor, templateImageColor, threshold=95):
			ret = 0.0, nlocation
		if mark >= 1:
			self.draw_rect(targetImg, nlocation)
		return ret

	def predict(self, targetImg, tmpImg, location: (tuple, list), factor: int = 4, exists: bool = True):
		"""
		predict target image and template image, check if they are in same label
		@param:
			targetImg: absolute path of target image or matrix object of image, must be in same shape and size with tmpImg
			tmpImg: absolute path of template image or matrix object of image, must be in same shape and size with targetImg
			location: four integers as a list to cut a rectangle area from targetImg, and compare with tmpImg
			factor(optional): the factor for enlarging
			exists(optional): check the icon exists if True, else check the icon not exists
		@return:
			float: similarity of two images
		"""
		if self.__tf is not None:
			targetImage, templateImage = self._load(targetImg, tmpImg, False)
			template_h, template_w = templateImage.shape[:2]
			if template_h > 200 or template_w > 300:
				tmpTargetImage = targetImage[location[1]:location[3], location[0]:location[2]]
				targetImgHSV = cv.cvtColor(tmpTargetImage, cv.COLOR_BGR2HSV)
				templateImgHSV = cv.cvtColor(templateImage, cv.COLOR_BGR2HSV)
				targetH, targetS, targetV = cv.split(targetImgHSV)
				templateH, templateS, templateV = cv.split(templateImgHSV)
				if numpy.mean(targetV) < 20 and numpy.mean(templateV) < 20 and numpy.max(targetV) < 20 and numpy.max(templateV) < 20:
					return 1.0, None, location
				return self.similarity(targetImage, templateImage), None, location
			else:
				locs = self.object_detect(targetImage, location, factor)
				label_name, similarity = self.__tf.predict(templateImage, threshold=0.85)
				logger.debug(f"the predict result of template image is: {label_name} and similarity is: {similarity}")
				for x1, y1, x2, y2 in locs:
					tmp_label_name, tmp_similarity = self.__tf.predict(targetImage[y1:y2, x1:x2], threshold=0.85)
					if tmp_label_name and tmp_label_name == label_name:
						logger.debug(f"target image and template image are in same type: '{tmp_label_name}' at location: "
									f"x1={x1}, y1={y1}, x2={x2}, y2={y2}")
						return (1.0, tmp_label_name, [x1, y1, x2, y2]) if exists else (0.0, None, None)
				return (0.0, None, None) if exists else (1.0, None, location)

	def compare(self, targetImg, tmpImg, gray: bool = False, threshold: int = -1, **kwargs):
		"""
		compare two images pixel by pixel using algorithms to speed up
		there are four methods of comparison:
			1."includes" passed in as param, then compare one or more than one rectangle areas selected from "targetImg" and "tmpImg"
			2."excludes" passed in as param, then set one or more than one rectangle areas to White in "targetImg" and "tmpImg",
										and then compare "targetImg" and "tmpImg"
			3.directly compare two images, "gray" and "threshold" could be set before comparison
			4."location" passed in as param, then use tmpImg to compare with selected rectangle area in targetImg
		@param:
			targetImg: absolute path of target image or matrix object of image, must be in same shape and size with tmpImg
			tmpImg: absolute path of template image or matrix object of image, must be in same shape and size with targetImg
			gray(optional): set two images to gray, default to False
			threshold(optional): set a threshold for gray image, filter background color or some other interference, used with "gray"
			includes(optional): a list of coordinates used for selecting areas from two images and compare
			excludes(optional): a list of coordinates used for setting rectangle areas to white, "includes" and "excludes" could
								not be used at the same time
			location(optional): four integers as a list to cut a rectangle area from targetImg, and compare with tmpImg
			offset(optional): for a same location in image, errors: [70, 92, 210] <-> [71, 92, 211] will be ignored if you set
								'offset' to 1, you will need to set 'offset' to 5 if you want to ignore error: [70, 92, 210] <-> [75, 92, 206]
			mark(optional): 0: no rectangle area will be marked
							1: specified areas will be marked with rectangles in targetImg (default)
							2: specified areas will be marked with rectangles in tmpImg
							3: specified areas will be marked with rectangles in both images
			filter(optional): used for removing background, 'threshold' must be set, can not compatible with 'includes' or 'excludes'
							True: remove background
							False(default): do nothing
			reverse(optional): 'filter' must be set, used to reverse the result of 'filter'
							True: remove foreground
							False(default): remove background
		@return:
			see self._compare_include_areas if "includes" passed in as param
			tuple: (a number between 0 and 1,
					tuple(start_x, start_y, end_x, end_y)
					) if "excludes" passed in as param
			tuple: (a number between 0 and 1,
					tuple(start_x, start_y, end_x, end_y)
					) if neither "includes" nor "excludes" passed in as param
		"""
		# check parameter 'mark'
		if "mark" in kwargs and isinstance(kwargs["mark"], int):
			mark = kwargs["mark"]
			if mark < 0 or mark > 3:
				mark = 1
		else:
			mark = 1
		# check parameter 'offset'
		if "offset" in kwargs and isinstance(kwargs["offset"], int) and kwargs["offset"] > 0:
			offset = kwargs["offset"]
		else:
			offset = 0
		# check parameter 'filter'
		if "filter" in kwargs and isinstance(kwargs["filter"], (str, bool)) and str(kwargs["filter"]).lower() == "true":
			filter_ = True
		else:
			filter_ = False
		# check parameter 'reverse'
		if "reverse" in kwargs and isinstance(kwargs["reverse"], (str, bool)) and str(kwargs["reverse"]).lower() == "true":
			reverse = True
		else:
			reverse = False

		# call self._compare_include_areas if param "includes" found in kwargs
		if "includes" in kwargs and "excludes" not in kwargs:
			return self._compare_include_areas(targetImg, tmpImg, kwargs["includes"], gray=gray, threshold=threshold, offset=offset, mark=mark)
		# call self._compare_exclude_areas if param "includes" found in kwargs
		elif "excludes" in kwargs and "includes" not in kwargs:
			return self._compare_exclude_areas(targetImg, tmpImg, kwargs["excludes"], gray=gray, threshold=threshold, offset=offset, mark=mark)
		# directly compare two images, gray and threshold could be set before comparison
		else:
			# read image
			targetImage, tmpImage = self._load(targetImg, tmpImg)
			if filter_:
				if 0 < threshold < 255:
					targetImage = self.remove_background(image=targetImage, threshold=threshold, reverse=reverse)
					tmpImage = self.remove_background(image=tmpImage, threshold=threshold, reverse=reverse)
			elif gray:
				targetImage, tmpImage = self._load(targetImg, tmpImg, True)
				if 0 < threshold < 255:
					ret, targetImage = cv.threshold(targetImage, threshold, 255, cv.THRESH_BINARY)
					ret, tmpImage = cv.threshold(tmpImage, threshold, 255, cv.THRESH_BINARY)
			location = (0, 0, tmpImage.shape[1], tmpImage.shape[0])
			if "location" in kwargs and isinstance(kwargs["location"], (list, tuple)) and len(kwargs["location"]) == 4:
				location = [int(x) for x in kwargs["location"]]
				targetImage = self.cut(targetImage, *location)
				if mark >= 1:
					self.draw_rect(targetImg, location)

			result = self._matrix_match(targetImage, tmpImage, offset=offset)
			return result["percent"], location

	def search(self, targetImg, tmpImg, method: str = "matrix", offset: int = 0, mark: int = 1):
		"""
		use "tmpImg" as template to find the best match in "targetImg", there are two ways to use search:
			method="matrix": provided by liluo@noboauto.com, faster than "template" most times
			method="template": provided by opencv, more stable
		@param:
			targetImg: absolute path of target image or matrix object of image
			tmpImg: absolute path of template image or matrix object of image, must be smaller than targetImg, used as a template
			method(optional): two values are available: "matrix"(default) and "template"
				matrix: default value, use "self._matrix_search" as main search method
				template: use "self._template_search" as main search method
				others: any value not in ("matrix", "template") will be set to "template"
			offset(optional): for a same location in image, errors: [70, 92, 210] <-> [71, 92, 211] will be ignored if you set
				'offset' to 1, you will need to set 'offset' to 5 if you want to ignore error: [70, 92, 210] <-> [75, 92, 204]
			mark(optional): 0: no rectangle area will be marked
							1: best matched area will be marked with a rectangle in targetImg (default)
							2: reserved
							3: reserved
		@return:
			tuple: (a number between 0 and 1,
					tuple(start_x, start_y, end_x, end_y)
					)
		"""
		if method.lower() == "matrix":
			result = self._matrix_search(targetImg, tmpImg, offset=offset, mark=mark)
		else:
			result = self._template_search(targetImg, tmpImg, offset=offset, mark=mark)
		return result["percent"], result["location"]

	@staticmethod
	def similarity(targetImg, TmpImg):
		"""
		use hanming distance arithmetic to compare the similarity of two images, just for fuzzy compare
		two images could be in different size and shape
		@param:
			targetImg: absolute path of target image or matrix object of image
			tmpImg: absolute path of template image or matrix object of image
		@return:
			float, between 0 and 1, 1 means perfect match and 0 means no similarity
		"""

		def p_hash(image):
			"""calculate hash code for image"""
			# read image as gray scale and resize image to 64x64
			img = cv.imdecode(numpy.fromfile(image, dtype=numpy.uint8), cv.IMREAD_COLOR) if isinstance(image, str) and os.path.exists(image) else image
			if len(img.shape) == 3 and img.shape[2] == 3:
				img = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
			img = cv.resize(img, (64, 64), interpolation=cv.INTER_CUBIC)

			# create data list
			height, width = img.shape[:2]
			vis0 = numpy.zeros((height, width), numpy.float32)
			vis0[:height, :width] = img

			# transfer to dct
			vis1 = cv.dct(cv.dct(vis0))
			vis1.resize(32, 32)
			img_list = [x for item in vis1 for x in item]

			# calculate average value
			avg = sum(img_list) * 1. / len(img_list)
			avg_list = ['0' if i < avg else '1' for i in img_list]

			# calculate hash value
			return ''.join(['%x' % int(''.join(avg_list[x:x + 4]), 2) for x in range(0, 32 * 32, 4)])

		targetHash = p_hash(targetImg)
		tmpHash = p_hash(TmpImg)
		similar = 1 - sum([ch1 != ch2 for ch1, ch2 in zip(targetHash, tmpHash)]) / (32 * 32 / 4)
		return similar

	@staticmethod
	def draw_rect(image, *loc):
		"""
		draw one or more than one rectangles in "image"
		@param:
			image: absolute path of a image or matrix of image
			loc: one or a serial of locations
		@return:
			the return value depends on the input, path will be returned if path is passed in, else matrix will be returned
			str, the path of marked image
			matrix, matrix for marked image
		@example:
			draw_rect("D:/xxx/xxx/xxx.png", (0, 0, 50, 50))
			draw_rect("D:/xxx/xxx/xxx.png", (0, 0, 50, 50), (100, 100, 200, 200), (200, 200, 300, 300))
		"""
		logger.debug(f"drawing rectangle for target image")
		enlarge_pixels = 3
		img = cv.imdecode(numpy.fromfile(image, dtype=numpy.uint8), cv.IMREAD_COLOR) if isinstance(image, str) and os.path.exists(image) else image
		rectangleColor = (0, 255, 255) if len(img.shape) == 3 else 255
		for L in loc:
			if isinstance(L, (tuple, list)) and len(L) == 4:
				L = list(L)
				L[0] = L[0] - enlarge_pixels
				L[1] = L[1] - enlarge_pixels
				L[2] = L[2] + enlarge_pixels
				L[3] = L[3] + enlarge_pixels
				img = cv.rectangle(img, tuple(L[:2]), tuple(L[2:]), rectangleColor, 1)
			else:
				logger.warning(f"coordinate: {L} must be a Tuple or List and has a length 4")
		if isinstance(image, str) and os.path.exists(image):
			# cv.imwrite(image, img)
			cv.imencode('.png', img)[1].tofile(image)
			return image
		else:
			return img

	@staticmethod
	def save(image, path: str, name: str = None):
		"""
		save a matrix as image
		@param:
			image: matrix object of image, should not be absolute path of image file
			path: a path for saving image matrix
			name: specify file name for image, None stands for default name with timestamp appended
		@return:
			str, absolute path of image file saved
		"""
		if not os.path.exists(path):
			logger.error(f"could not save image to a nonexistent path: <{path}>")
			return
		if not name:
			name = "image"

		now = datetime.datetime.now()
		ts = f"{now.year}_{now.month}_{now.day}-{now.hour}_{now.minute}_{now.second}_{now.microsecond}"
		file_name = os.path.join(path, f"{name}-{ts}.png")

		cv.imencode('.png', image)[1].tofile(file_name)
		return file_name

	@staticmethod
	def merge(targetImg, tmpImg, mergedPath: str = None):
		"""
		merge two images into one and return merged image's path if "mergedPath" specified
		@param:
			targetImg: absolute path of target image or matrix of target image
			tmpImg: absolute path of template image or matrix of template image
			mergedPath(optional): the path to store merged image
		@return:
			str, the path of merged image, if "mergedPath" has been set
			matrix, matrix of merged image, if "mergedPath" has not been set
			None, if one of "targetImg" and "tmpImg" is not an image at all
		"""
		# load image
		targetImg = cv.imdecode(numpy.fromfile(targetImg, dtype=numpy.uint8), cv.IMREAD_COLOR) if isinstance(targetImg, str) and os.path.exists(targetImg) else targetImg
		tmpImg = cv.imdecode(numpy.fromfile(tmpImg, dtype=numpy.uint8), cv.IMREAD_COLOR) if isinstance(tmpImg, str) and os.path.exists(tmpImg) else tmpImg
		# check if two image or matrix are in same shape and size
		targetShape = targetImg.shape
		tmpShape = tmpImg.shape
		targetWidth, targetHeight = targetShape[1], targetShape[0]
		tmpWidth, tmpHeight = tmpShape[1], tmpShape[0]
		if tmpHeight > targetHeight:
			targetImg, tmpImg = tmpImg, targetImg
			targetHeight, tmpHeight = tmpHeight, targetHeight
			targetWidth, tmpWidth = tmpWidth, targetWidth

		# define the color of a delimiter image for two merged images
		delimiterWidth = 30
		delimiterColor = [0, 0, 255]
		delimiterGray = 255

		# check if image data are available
		if len(targetShape) < 2 or len(targetShape) > 3 or len(tmpShape) < 2 or len(tmpShape) > 3:
			logger.error(f"input param is not images, nothing will be merged.")
			return None

		# two images are gray
		if len(targetShape) == len(tmpShape) == 2:
			container = numpy.full((targetHeight, delimiterWidth + tmpWidth + delimiterWidth), delimiterGray, dtype=numpy.uint8)
			container = numpy.hstack((targetImg, container))
			startW = targetWidth + delimiterWidth
			startH = (targetHeight - tmpHeight) // 2
			container[startH: startH + tmpHeight, startW: startW + tmpWidth] = tmpImg
		else:
			# target image is gray and template image is colored
			if len(targetShape) == 2:
				targetImg = cv.cvtColor(targetImg, cv.COLOR_GRAY2BGR)
			# template image is gray and target image is colored
			elif len(tmpShape) == 2:
				tmpImg = cv.cvtColor(tmpImg, cv.COLOR_GRAY2BGR)
			containerB = numpy.full((targetHeight, delimiterWidth + tmpWidth + delimiterWidth), delimiterColor[0], dtype=numpy.uint8)
			containerG = numpy.full((targetHeight, delimiterWidth + tmpWidth + delimiterWidth), delimiterColor[1], dtype=numpy.uint8)
			containerR = numpy.full((targetHeight, delimiterWidth + tmpWidth + delimiterWidth), delimiterColor[2], dtype=numpy.uint8)
			container = cv.merge((containerB, containerG, containerR))
			container = numpy.hstack((targetImg, container))
			startW = targetWidth + delimiterWidth
			startH = (targetHeight - tmpHeight) // 2
			container[startH: startH + tmpHeight, startW: startW + tmpWidth] = tmpImg

		if mergedPath:
			# cv.imwrite(mergedPath, container)
			cv.imencode('.png', container)[1].tofile(mergedPath)
			return mergedPath
		return container

	@staticmethod
	def remove_background(image, threshold: int = 128, reverse: bool = False):
		"""
		remove background from image
		@param:
			image: absolute path of image or matrix object of image
			threshold: threshold use for filtering background, default: 128
			reverse: True: filter foreground, False(default): filter background
		@return:
			matrix object of image, could be saved directly or used for comparison
		"""
		img = cv.imdecode(numpy.fromfile(image, dtype=numpy.uint8), cv.IMREAD_COLOR) if isinstance(image, str) and os.path.exists(image) else image
		shape = img.shape
		img_mask = copy.deepcopy(img)
		if len(shape) == 3 and shape[2] == 3:
			img_mask = cv.cvtColor(img_mask, cv.COLOR_BGR2GRAY)
		ret, img_mask = cv.threshold(img_mask, threshold, 255, cv.THRESH_BINARY)
		if reverse:
			img_mask = cv.bitwise_not(img_mask)
		img = cv.bitwise_and(img, img, mask=img_mask)

		return img

	def _compare_exclude_areas(
			self,
			targetImg,
			tmpImg,
			excludes: (list, tuple),
			gray: bool = False,
			threshold: int = -1,
			offset: int = 0,
			mark: int = 1
	):
		"""
		set one or more than one rectangle areas to White in "targetImg" and "tmpImg", and then compare "targetImg" and "tmpImg"
		this method is used for filtering some unimportant areas and compare the rest of images
		@param:
			targetImg: absolute path of target image or matrix object of image, must be in same shape and size with tmpImg
			tmpImg: absolute path of template image or matrix object of image, must be in same shape and size with targetImg
			excludes: a list of coordinates used for setting rectangle areas to white
			gray(optional): set two images to gray, default to False
			threshold(optional): set a threshold for gray image, filter background color or some other interference, used with "gray"
			offset(optional): for a same location in image, errors: [70, 92, 210] <-> [71, 92, 211] will be ignored if you set
				'offset' to 1, you will need to set 'offset' to 5 if you want to ignore error: [70, 92, 210] <-> [75, 92, 204]
			mark(optional): 0: no rectangle area will be marked
							1: specified areas will be marked with rectangles in targetImg (default)
							2: specified areas will be marked with rectangles in tmpImg
							3: specified areas will be marked with rectangles in both images
		@return:
			tuple: (a number between 0 and 1,
					tuple(start_x, start_y, end_x, end_y)
					)
		@examples:
			1._compare_exclude_areas("D:/xxx.png", "D:/yyy.png", [0, 0, 10, 10]) -> (0.997, (0, 0, 1920, 720))
			2._compare_exclude_areas("D:/xxx.png", "D:/yyy.png", [(0, 0, 10, 10), (50, 60, 100, 110)]) -> (0.997, (0, 0, 1920, 720))
			3._compare_exclude_areas("D:/xxx.png", "D:/yyy.png", [0, 0, 10, 10], True) -> (0.997, (0, 0, 1920, 720))
			4._compare_exclude_areas("D:/xxx.png", "D:/yyy.png", [0, 0, 10, 10], True, 200) -> (0.997, (0, 0, 1920, 720))
		"""
		if mark < 0 or mark > 3:
			mark = 1

		if all([isinstance(x, int) for x in excludes]):
			excludeList = [excludes]
		elif all([isinstance(x, (list, tuple)) for x in excludes]):
			excludeList = excludes
		else:
			logger.warning(f"data struct of excludes must be [1, 2, 3, 4] or [[1, 2, 3, 4], [5, 6, 7, 8]], other data will be ignored")
			return []

		# read image
		targetImage, tmpImage = self._load(targetImg, tmpImg)
		if gray:
			targetImage, tmpImage = self._load(targetImg, tmpImg, True)
			if 0 < threshold < 255:
				ret, targetImage = cv.threshold(targetImage, threshold, 255, cv.THRESH_BINARY)
				ret, tmpImage = cv.threshold(tmpImage, threshold, 255, cv.THRESH_BINARY)
			else:
				logger.warning(f"threshold value: {threshold} is invalid, must be in (0, 255)")

		for item in excludeList:
			if not all([isinstance(x, int) for x in item]) or len(item) != 4:
				logger.warning(f"coordinate: {item} is not available, will be ignored")
				continue
			if not self.__check_border(targetImage.shape, item) or not self.__check_border(tmpImage.shape, item):
				logger.warning(f"coordinate: {item} beyond the border of image, will be ignored")
				continue
			if gray:
				targetImage[item[1]: item[3], item[0]: item[2]] = 255
				tmpImage[item[1]: item[3], item[0]: item[2]] = 255
			else:
				targetImage[item[1]: item[3], item[0]: item[2]] = [255, 255, 255]
				tmpImage[item[1]: item[3], item[0]: item[2]] = [255, 255, 255]
		# draw rectangles in targetImg
		if mark == 1:
			self.draw_rect(targetImg, *excludeList)
		elif mark == 2:
			self.draw_rect(tmpImg, *excludeList)
		elif mark == 3:
			self.draw_rect(targetImg, *excludeList)
			self.draw_rect(tmpImg, *excludeList)

		result = self._matrix_match(targetImage, tmpImage, offset=offset)
		return result["percent"], (0, 0, targetImage.shape[1], targetImage.shape[0])

	def _compare_include_areas(
			self,
			targetImg,
			tmpImg,
			includes: (list, tuple),
			gray: bool = False,
			threshold: int = -1,
			offset: int = 0,
			mark: int = 1
	):
		"""
		compare one or more than one rectangle areas selected from "targetImg" and "tmpImg"
		@param:
			targetImg: absolute path of target image or matrix object of image, must be in same shape and size with tmpImg
			tmpImg: absolute path of template image or matrix object of image, must be in same shape and size with targetImg
			includes: a list of coordinates used for selecting areas from two images and compare
			gray(optional): set two images to gray, default to False
			threshold(optional): set a threshold for gray image, filter background color or some other interference, used with "gray"
			offset(optional): for a same location in image, errors: [70, 92, 210] <-> [71, 92, 211] will be ignored if you set
				'offset' to 1, you will need to set 'offset' to 5 if you want to ignore error: [70, 92, 210] <-> [75, 92, 204]
			mark(optional): 0: no rectangle area will be marked
							1: specified areas will be marked with rectangles in targetImg (default)
							2: specified areas will be marked with rectangles in tmpImg
							3: specified areas will be marked with rectangles in both images
		@return:
			includes = [1, 2, 3, 4]
			return = (percent, (1, 2, 3, 4))
			or:
			includes = [[1, 2, 3, 4], [5, 6, 7, 8], ...]
			return = [(percent1, (1, 2, 3, 4)), (percent2, (5, 6, 7, 8)), ...]
		@examples:
			1._compare_include_areas("D:/xxx.png", "D:/yyy.png", [0, 0, 10, 10]) -> (0.997, (0, 0, 10, 10))
			2._compare_include_areas("D:/xxx.png", "D:/yyy.png", [(0, 0, 10, 10), (50, 60, 100, 110)]) ->
				[(0.999, (0, 0, 10, 10)), (0.589, (50, 60, 100, 110))]
			3._compare_include_areas("D:/xxx.png", "D:/yyy.png", [0, 0, 10, 10], True) -> (0.997, (0, 0, 10, 10))
			4._compare_include_areas("D:/xxx.png", "D:/yyy.png", [0, 0, 10, 10], True, 200) -> (0.997, (0, 0, 10, 10))
		"""
		if mark < 0 or mark > 3:
			mark = 1

		if all([isinstance(x, int) for x in includes]):
			includeList = [includes]
		elif all([isinstance(x, (list, tuple)) for x in includes]):
			includeList = includes
		else:
			logger.warning(f"data struct of includes must be [1, 2, 3, 4] or [[1, 2, 3, 4], [5, 6, 7, 8]], other data will be ignored")
			return []

		# read image
		targetImage, tmpImage = self._load(targetImg, tmpImg)
		if gray:
			targetImage, tmpImage = self._load(targetImg, tmpImg, True)
			if 0 < threshold < 255:
				ret, targetImage = cv.threshold(targetImage, threshold, 255, cv.THRESH_BINARY)
				ret, tmpImage = cv.threshold(tmpImage, threshold, 255, cv.THRESH_BINARY)
			else:
				logger.warning(f"threshold value: {threshold} is invalid, must be in (0, 255)")

		# resultList: to store comparison results
		resultList = []
		for item in includeList:
			if not all([isinstance(x, int) for x in item]) or len(item) != 4:
				logger.warning(f"coordinate: {item} is not available, will be ignored")
				resultList.append((None, None))
				continue
			if not self.__check_border(targetImage.shape, item) or not self.__check_border(tmpImage.shape, item):
				logger.warning(f"coordinate: {item} beyond the border of image, will be ignored")
				resultList.append((None, None))
				continue
			selectedTarget = self.cut(targetImage, *item)
			selectedTmp = self.cut(tmpImage, *item)
			selectedRes = self._matrix_match(selectedTarget, selectedTmp, offset=offset)
			resultList.append((selectedRes["percent"], tuple(item)))

		# draw rectangles in targetImg
		if mark == 1:
			self.draw_rect(targetImg, *includeList)
		elif mark == 2:
			self.draw_rect(tmpImg, *includeList)
		elif mark == 3:
			self.draw_rect(targetImg, *includeList)
			self.draw_rect(tmpImg, *includeList)

		if len(resultList) == 1 and all([isinstance(x, int) for x in includes]):
			return resultList[0]
		return resultList

	def _template_search(self, targetImg, tmpImg, offset: int = 0, mark: int = 1):
		"""
		use template match of opencv, use tmpImg as template to find the best match in targetImg
		@param:
			targetImg: absolute path of target image or matrix object of image
			tmpImg: absolute path of template image or matrix object of image, must be smaller than targetImg, used as a template
			offset(optional): for a same location in image, errors: [70, 92, 210] <-> [71, 92, 211] will be ignored if you set
				'offset' to 1, you will need to set 'offset' to 5 if you want to ignore error: [70, 92, 210] <-> [75, 92, 204]
			mark(optional): 0: no rectangle area will be marked
							1: best matched area will be marked with a rectangle in targetImg (default)
							2: reserved
							3: reserved
		@return:
			dict: {"percent": float, the similarity rate of two images, example: 0.991234
					"location": tuple (start_x, start_y, end_x, end_y), the x and y coordinates of best match position in targetImg
					}
		"""
		# normalize the mark
		if mark < 0 or mark > 1:
			mark = 1

		targetImgColor, tmpImgColor = self._load(targetImg, tmpImg)
		height, width = tmpImgColor.shape[:2]
		maxMatch = None
		for md in self.templateMethods:
			# calculate the best match with three different methods
			result = cv.matchTemplate(targetImgColor, tmpImgColor, md)
			min_val, max_val, min_loc, max_loc = cv.minMaxLoc(result)
			# return result if perfect matched with method TM_SQDIFF_NORMED
			if md == cv.TM_SQDIFF_NORMED and 0 <= min_val <= 0.000001:
				maxMatch = {"percent": 1.0, "location": (min_loc[0], min_loc[1], min_loc[0] + width, min_loc[1] + height)}
			# return result if perfect matched with method TM_CCORR_NORMED
			elif (md == cv.TM_CCORR_NORMED or md == cv.TM_CCOEFF_NORMED) and 0.999999 <= max_val <= 1.000001:
				maxMatch = {"percent": 1.0, "location": (max_loc[0], max_loc[1], max_loc[0] + width, max_loc[1] + height)}
			# calculate the best match in three methods independently and return the best one
			else:
				if md == cv.TM_SQDIFF_NORMED:
					loc = min_loc
				else:
					loc = max_loc
				targetImgSliced = self.cut(targetImgColor, loc[0], loc[1], loc[0] + width, loc[1] + height)
				matchRes = self._matrix_match(targetImgSliced, tmpImgColor, offset=offset)
				if maxMatch:
					if matchRes["percent"] > maxMatch["percent"]:
						maxMatch.update({"percent": matchRes["percent"], "location": (loc[0], loc[1], loc[0] + width, loc[1] + height)})
				else:
					maxMatch = {"percent": matchRes["percent"], "location": (loc[0], loc[1], loc[0] + width, loc[1] + height)}

		# draw a rectangle in targetImg
		if mark == 1:
			self.draw_rect(targetImg, maxMatch["location"])
		return maxMatch

	def _matrix_search(self, targetImg, tmpImg, offset: int = 0, mark: int = 1):
		"""
		use tmpImg as template and search in targetImg to find a best match, this is matrix search not template match
		@param:
			targetImg: absolute path of target image  or matrix object of image
			tmpImg: absolute path of template image  or matrix object of image, must be smaller than targetImg, used as a template
			offset(optional): for a same location in image, errors: [70, 92, 210] <-> [71, 92, 211] will be ignored if you set
				'offset' to 1, you will need to set 'offset' to 5 if you want to ignore error: [70, 92, 210] <-> [75, 92, 204]
			mark(optional): 0: no rectangle area will be marked
							1: best matched area will be marked with a rectangle in targetImg (default)
							2: reserved
							3: reserved
		@return:
			dict: {"totalPoints": int, the total points of matrix
					"diffPoints": int, count of points which are different between targetImg and tmpImg
					"percent": float, the similarity rate of two matrix, example: 0.991234
					"location": tuple (start_x, start_y, end_x, end_y), the x and y coordinates of best match position in targetImg
					}
		"""
		# normalize the mark
		if mark < 0 or mark > 1:
			mark = 1

		# gray images for base and target, used to find out the gray histogram and get the best comparison points
		targetImgGray, tmpImgGray = self._load(targetImg, tmpImg, gray=True)
		if self.__check_shape(targetImgGray, tmpImgGray) != 1:
			raise AttributeError(f"to use image search, target image:'{tmpImg}' must be smaller than base image:'{targetImg}'")

		# a backup for base and target images, used for colored comparison later
		targetImgColor, tmpImgColor = self._load(targetImg, tmpImg)

		# calculate histogram of base and target images
		baseHistogram = cv.calcHist([targetImgGray], [0], None, [256], [0, 255])
		targetHistogram = cv.calcHist([tmpImgGray], [0], None, [256], [0, 255])

		# data struct is [(gray_level, corresponding_points_count), (gray_level, corresponding_points_count), ...]
		baseHistogram = [(i, int(x[0])) for i, x in enumerate(baseHistogram) if int(x[0]) > 0]
		targetHistogram = [(i, int(x[0])) for i, x in enumerate(targetHistogram) if int(x[0]) > 0]

		# find a gray level that exists in base image and target image, the corresponding count of points of this
		# gray level must be as small as possible
		baseHistSorted = sorted(baseHistogram, key=lambda x: x[1])
		targetHistSortedGrayLevels = [x[0] for x in targetHistogram]
		minMatchGrayLevel = None
		for index, value in baseHistSorted:
			if index in targetHistSortedGrayLevels:
				minMatchGrayLevel = index
				break

		# calculate all coordinates of selected gray level in base and target images
		baseGrayPoints = numpy.where(targetImgGray == minMatchGrayLevel)
		targetGrayPoints = numpy.where(tmpImgGray == minMatchGrayLevel)
		baseGrayPoints = [(x, y) for x, y in zip(baseGrayPoints[1], baseGrayPoints[0])]
		targetGrayPoints = [(x, y) for x, y in zip(targetGrayPoints[1], targetGrayPoints[0])]

		targetGrayPoints = sorted(targetGrayPoints, key=lambda x: x[0] + x[1])
		selectedTargetPoint = targetGrayPoints[0]

		# start to compare target image with all images corresponding to "baseGrayPoints" and find a best match
		tmpImgShape = tmpImgColor.shape
		bestMatch = {}
		for x, y in baseGrayPoints:
			# get a same size of image with target image from base image, use shift coordinates based on "baseGrayPoints"
			start_x = x - selectedTargetPoint[0]
			start_y = y - selectedTargetPoint[1]
			end_x = start_x + tmpImgShape[1]
			end_y = start_y + tmpImgShape[0]
			if not self.__check_border(targetImgColor.shape, [start_x, start_y, end_x, end_y]):
				continue
			tmpImg = self.cut(targetImgColor, start_x, start_y, end_x, end_y)
			matchRes = self._matrix_match(tmpImg, tmpImgColor, offset=offset)
			if bestMatch:
				if matchRes["percent"] > bestMatch["percent"]:
					bestMatch.update({**matchRes, "location": (start_x, start_y, end_x, end_y)})
			else:
				bestMatch.update({**matchRes, "location": (start_x, start_y, end_x, end_y)})

		# draw a rectangle in targetImg
		if mark == 1:
			self.draw_rect(targetImg, bestMatch["location"])
		return bestMatch

	def _matrix_match(self, targetMat, tmpMat, offset: int = 0):
		"""
		compare two matrix of images which are in same shape and size, available for both gray scale images and colored images
		@param:
			targetMat: target matrix of image, must be in same shape and size with tmpMat
			tmpMat: template matrix of image, must be in same shape and size with targetMat
			offset(optional): for a same location in image, errors: [70, 92, 210] <-> [71, 92, 211] will be ignored if you set
				'offset' to 1, you will need to set 'offset' to 5 if you want to ignore error: [70, 92, 210] <-> [75, 92, 204]
		@return:
			dict, {"totalPoints": int, the total points of matrix
					"diffPoints": int, count of points which are different between targetMat and tmpMat
					"percent": float, the similarity rate of two matrix, example: 0.991234
					}
		"""
		if self.__check_shape(targetMat, tmpMat) != 0:
			raise AttributeError(f"two images or matrix must be in same shape and size")
		gray = True if len(targetMat.shape) == len(tmpMat.shape) == 2 else False
		totalPoints = targetMat.shape[0] * targetMat.shape[1]
		# compare gray scale image
		if gray:
			# compare
			deltaArray = numpy.array(targetMat, dtype=numpy.int) - numpy.array(tmpMat, dtype=numpy.int)
			if offset > 0:
				deltaPoints = numpy.sum(numpy.abs(deltaArray) > offset)
			else:
				deltaPoints = numpy.count_nonzero(deltaArray)
		# compare colored image
		else:
			# split colored image into B,G,R channels
			base_b, base_g, base_r = cv.split(targetMat)
			target_b, target_g, target_r = cv.split(tmpMat)
			# compare three channels independently
			delta_b = numpy.array(base_b, dtype=numpy.int) - numpy.array(target_b, dtype=numpy.int)
			delta_g = numpy.array(base_g, dtype=numpy.int) - numpy.array(target_g, dtype=numpy.int)
			delta_r = numpy.array(base_r, dtype=numpy.int) - numpy.array(target_r, dtype=numpy.int)
			# combine results of three channels
			if offset > 0:
				delta_b = numpy.where(numpy.abs(delta_b) > offset, delta_b, 0)
				delta_g = numpy.where(numpy.abs(delta_g) > offset, delta_g, 0)
				delta_r = numpy.where(numpy.abs(delta_r) > offset, delta_r, 0)
			delta = numpy.abs(delta_b) + numpy.abs(delta_g) + numpy.abs(delta_r)
			# get diff points
			deltaPoints = numpy.count_nonzero(delta)
		return {"totalPoints": totalPoints, "diffPoints": deltaPoints, "percent": (totalPoints - deltaPoints) / totalPoints}

	def _multi_threshold(self, imgMat, thresholdStep: int = 64, graySet: int = 0):
		"""
		multi threshold: set a serial of threshold which split by parameter "threshold" and set gray level values to threshold list.
		for example: threshold=64, then a threshold list will be created: [0, 64, 128, 196, 255], if a point's gray level
		is 63 then it will be set to 0, and 2 to 0, 90 to 64, 127 to 64, 150 to 196, 200 to 255 and etc.
		the main purpose of this method is to reduce the count of gray level and disperse original gray levels to newly created gray levels
		@param:
			imgMat: matrix object of image
			thresholdStep: step for threshold list, from 0 to 255
			graySet: 0 for set gray value to the nearest lower threshold if the gray value was smaller than 128,
						else set gray value to the nearest upper threshold
					1 for set gray value to a middle value of two thresholds
		@return:
			numpy.ndarray, return a matrix object of image
		"""
		if thresholdStep <= 0 or thresholdStep >= 255:
			logger.error(f"thresholdStep: <{thresholdStep}> unsupported")
			return
		if len(imgMat.shape) != 2:
			logger.error(f"only image in gray scale could be used for calculating multi threshold")
			return

		gray_levels = list(range(256))
		thresholds = gray_levels[::thresholdStep]
		for thd1, thd2 in zip(thresholds, thresholds[1:] + [255]):
			if graySet == 0:
				if thd1 >= 128:
					imgMat = numpy.where((imgMat > thd1) & (imgMat <= thd2), thd2, imgMat)
				elif thd1 < 128 <= thd2:
					imgMat = numpy.where((imgMat >= thd1) & (imgMat < thd2), (thd1 + thd2) // 2, imgMat)
				else:
					imgMat = numpy.where((imgMat >= thd1) & (imgMat < thd2), thd1, imgMat)
			else:
				if thd2 == 255:
					imgMat = numpy.where((imgMat >= thd1) & (imgMat <= thd2), (thd1 + thd2) // 2, imgMat)
				else:
					imgMat = numpy.where((imgMat >= thd1) & (imgMat < thd2), (thd1 + thd2) // 2, imgMat)

		return imgMat

	def cut(self, image, sx: int, sy: int, ex: int, ey: int, file: str = None):
		"""
		cut a small image from a big image or matrix
		@param:
			image: absolute path of image or matrix object of a image
			sx: x axis of start point
			sy: y axis of start point
			ex: x axis of end point
			ey: y axis of end point
			file:(optional) save selected area as new image if file specified
		@return:
			matrix, selected area of image
		"""
		img = cv.imdecode(numpy.fromfile(image, dtype=numpy.uint8), cv.IMREAD_COLOR) if isinstance(image, str) and os.path.exists(image) else image
		imgShape = img.shape
		if not self.__check_border(imgShape, [sx, sy, ex, ey]):
			return img
		selected = img[sy:ey, sx:ex]
		if file:
			# cv.imwrite(file, selected)
			cv.imencode('.png', selected)[1].tofile(file)

		return selected

	@staticmethod
	def _load(targetImg, tmpImg, gray: bool = False):
		"""
		load target image and template image as matrix, used for image comparison or search
		@param:
			targetImg: absolute path or matrix object, target image stored on local machine
			tmpImg: absolute path or matrix object, template image downloaded from camera or video or other devices, compared with base image
			gray: load images as gray scale, default to False
		@return:
			tuple, matrix of target image and template image
		"""
		targetImg = cv.imdecode(numpy.fromfile(targetImg, dtype=numpy.uint8), cv.IMREAD_COLOR) if isinstance(targetImg, str) and os.path.exists(targetImg) else targetImg
		tmpImg = cv.imdecode(numpy.fromfile(tmpImg, dtype=numpy.uint8), cv.IMREAD_COLOR) if isinstance(tmpImg, str) and os.path.exists(tmpImg) else tmpImg
		if gray:
			if len(targetImg.shape) == 3 and targetImg.shape[2] == 3:
				targetImg = cv.cvtColor(targetImg, cv.COLOR_BGR2GRAY)
			if len(tmpImg.shape) == 3 and tmpImg.shape[2] == 3:
				tmpImg = cv.cvtColor(tmpImg, cv.COLOR_BGR2GRAY)

		return targetImg, tmpImg

	@staticmethod
	def __check_border(imgShape: tuple, border: list) -> bool:
		"""
		check if the border of a area is available or not
		@param:
			imgShape: shape of image
			border: a list stores coordinates for a rectangle: [start_x, start_y, end_x, end_y]
		@return:
			bool, True means border is available, False means border is not available
		"""
		b = border
		if not imgShape or len(imgShape) < 2:
			logger.warning(f"shape of image is not available")
			return False
		width = imgShape[1]
		height = imgShape[0]
		if len(b) != 4 and not all([isinstance(x, int) for x in b]):
			logger.warning(f"coordinates are not available: {b}")
			return False
		if (b[0] < 0 or b[1] < 0 or b[2] < 0 or b[3] < 0) \
			or (b[0] > width or b[2] > width or b[1] > height or b[3] > height):
			logger.warning(f"border overflowed: {b}")
			return False
		if b[0] >= b[2] or b[1] >= b[3]:
			logger.warning(f"selected area must be a rectangle")
			return False
		return True

	@staticmethod
	def __check_shape(targetImg, tmpImg):
		"""
		check the shape of target image and template image:
			target image and template image are in same shape and type, then start image comparison
			target image is bigger than template image and also in same type, then start search template image from target image
		@param:
			targetImg: absolute path of target image or matrix object of image
			tmpImg: absolute path of template image or matrix object of image
		@return:
			bool:
				0 stands for in same shape and size,
				1 stands for template image is smaller than target image
				-1 stands for the width of template image is bigger than target image but height is smaller, can not used for direct match
		"""
		targetImgShape = targetImg.shape
		tmpImgShape = tmpImg.shape
		if targetImgShape == tmpImgShape:
			return 0
		elif len(targetImgShape) == len(tmpImgShape):
			if len(targetImgShape) == 2:
				if targetImgShape[0] > tmpImgShape[0] and targetImgShape[1] > tmpImgShape[1]:
					return 1
			elif len(targetImgShape) == 3:
				if targetImgShape[0] > tmpImgShape[0] and targetImgShape[1] > tmpImgShape[1] and targetImgShape[2] == tmpImgShape[2]:
					return 1
		else:
			return -1

	def brightness(self, image, slice_: (list, tuple) = (0, 0), resolution: (tuple, list) = (1920, 720)):
		"""
		calculate the average brightness of image, result from 0 to 1000
		@param:
			image: absolute path of image or matrix object of image
			slice_: split the input image into slice_[0] x slice_[1] blocks and return brightnesses of these blocks
			resolution: resolution of image, default to 1920 * 720
		@return:
			list: average brightness of each block
		"""
		brightness = []

		img = cv.imdecode(numpy.fromfile(image, dtype=numpy.uint8), cv.IMREAD_COLOR) if isinstance(image, str) and os.path.exists(image) else image
		shape = img.shape
		if len(shape) == 3:
			img = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
		if len(slice_) != 2:
			logger.error(f"slice must be a tuple or list and length must be 2: <{slice_}>")
			return None
		if len(resolution) != 2 or resolution[0] <= 10 or resolution[1] <= 10:
			logger.error(f"resolution must be a tuple or list: <{resolution}>")
			return None
		if shape[0] > resolution[1] or shape[1] > resolution[0]:
			img = img[0: resolution[1], 0: resolution[0]]

		column, row = slice_
		width, height = resolution

		ave_img = copy.deepcopy(img)
		ave = numpy.average(ave_img)
		# logger.info(f"get average brightness of block: <(0, 0), ({width}, {height})> is: <{ave}>")
		brightness.append(((0, 0, width, height), round(ave, 0)))
		if column > 1 and row > 1:
			ws = [x * (width // column) for x in range(column)] + [width]
			hs = [x * (height // row) for x in range(row)] + [height]
			for x1, x2 in zip(ws[:-1], ws[1:]):
				for y1, y2 in zip(hs[:-1], hs[1:]):
					block = self.cut(img, x1, y1, x2, y2)
					max_bright = numpy.max(block)
					ave = numpy.average(block) if max_bright > 30 else 0
					# logger.info(f"get average brightness of block: <({x1}, {y1}), ({x2}, {y2})> is: <{ave}>")
					brightness.append(((x1, y1, x2, y2), round(ave, 0)))
			return brightness
		return brightness[0][1]

	@staticmethod
	def histogram(image):
		"""
		calculate histogram of image
		@param:
			image: absolute path of image or matrix object of image
		@return:
			list: a list of histogram
		"""
		img = cv.imdecode(numpy.fromfile(image, dtype=numpy.uint8), cv.IMREAD_COLOR) if isinstance(image, str) and os.path.exists(image) else image
		shape = img.shape
		if len(shape) == 3:
			img = cv.cvtColor(img, cv.COLOR_BGR2GRAY)

		# calculate histogram of image
		Histogram = cv.calcHist([img], [0], None, [256], [0, 255])
		Histogram = [int(x[0]) for i, x in enumerate(Histogram)]

		return Histogram


if __name__ == "__main__":
	I = Image(r"D:\Bruce\003_GIT\cluster\ACT\resource\train", r"D:\Bruce\003_GIT\cluster\ACT\config")
	target = r"C:\Users\GW00214435\Downloads\Snipaste_2021-08-24_11-01-52.png"
	cut_loc = [12, 177, 1873, 933]
	target = cv.imdecode(numpy.fromfile(target, dtype=numpy.uint8), cv.IMREAD_COLOR)
	target = I.resize_display(target, (1920, 720), cut_loc)
	template = r"D:\Bruce\003_GIT\cluster\ACT\resource\image\template\cap_Telltale_21.2.24\发动机系统故障指示灯_No8AT_ON(7, 359, 57, 409).png"
	loc = [7, 359, 57, 409]
	print(I.predict(target, template, loc))
