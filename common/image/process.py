#! /usr/bin/env python



"""
provide basic image processing
"""

try:
    from common.logger.logger import logger
except (ImportError, ModuleNotFoundError) as e:
    import logging as logger
import cv2 as cv
import numpy
import time
import copy
from skimage import feature
from skimage import metrics
from skimage import filters
from common.image.color import COLOR


class ImageProcessing:
    def __init__(self):
        pass

    @staticmethod
    def template_math(targetImgMat, templateImgMat):
        """
        match two images using template matching, images should be gray scale or colored
        shift of image pixel affects result a lot
        @param:
            targetImgMat: numpy.ndarray, matrix object of target image
            templateImgMat: numpy.ndarray, matrix object of template image
        @return:
            float: from 0 to 1
        """
        if targetImgMat.shape != templateImgMat.shape:
            logger.error(f"target image and template image must be in same shape: target shape={targetImgMat.shape}, template shape={templateImgMat.shape}")
            return 0
        sqdiff = cv.matchTemplate(targetImgMat, templateImgMat, cv.TM_SQDIFF_NORMED)
        ccorr = cv.matchTemplate(targetImgMat, templateImgMat, cv.TM_CCORR_NORMED)
        ccoeff = cv.matchTemplate(targetImgMat, templateImgMat, cv.TM_CCOEFF_NORMED)

        sqdiff_min_val, sqdiff_max_val, sqdiff_min_loc, sqdiff_max_loc = cv.minMaxLoc(sqdiff)
        sqdiff_min_val = 1 - sqdiff_min_val
        sqdiff_max_val = 1 - sqdiff_max_val
        ccorr_min_val, ccorr_max_val, ccorr_min_loc, ccorr_max_loc = cv.minMaxLoc(ccorr)
        ccoeff_min_val, ccoeff_max_val, ccoeff_min_loc, ccoeff_max_loc = cv.minMaxLoc(ccoeff)

        min_similarity = (sqdiff_min_val + ccorr_min_val + ccoeff_min_val) / 3
        max_similarity = (sqdiff_max_val + ccorr_max_val + ccoeff_max_val) / 3
        logger.debug(f"result of template math is: <min similarity={min_similarity}, max similarity={max_similarity}>")

        return max_similarity

    @staticmethod
    def feature_match(targetImgMat, templateImgMat):
        """
        match two images using feature matching, images should be gray scale or colored
        shift of image pixel may not affects the result
        @param:
            targetImgMat: numpy.ndarray, matrix object of target image
            templateImgMat: numpy.ndarray, matrix object of template image
        @return:
            float: from 0 to 1
        """
        def match(target, template):
            # logger.debug(f"using 'feature matching' to match images")
            # Initiate SIFT detector
            sift = cv.SIFT_create()
            # find the keypoints and descriptors with SIFT
            kp1, des1 = sift.detectAndCompute(target, None)
            kp2, des2 = sift.detectAndCompute(template, None)
            if des1 is None or des2 is None:
                logger.error(f"no feature point could be detected, skip")
                return 0.0

            FLANN_INDEX_KDTREE = 1
            index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
            search_params = dict(checks=50)

            flann = cv.FlannBasedMatcher(index_params, search_params)
            matches = flann.knnMatch(des1, des2, k=2)

            # store all the good matches as per Lowe's ratio test.
            good = []
            for m, n in matches:
                if m.distance < 0.75 * n.distance:
                    good.append(m)

            if len(good) > 10:
                result = round(len(good) / len(matches), 6)
                return result
            else:
                return 0.0

        if targetImgMat.shape != templateImgMat.shape:
            logger.error(f"target image and template image must be in same shape: target shape={targetImgMat.shape}, template shape={templateImgMat.shape}")
            return 0
        if len(targetImgMat.shape) == len(templateImgMat.shape) == 2:
            similarity = match(targetImgMat, templateImgMat)
            logger.debug(f"result of feature_matching is: <{similarity}>")
            return similarity
        targetImgMatB, targetImgMatG, targetImgMatR = cv.split(targetImgMat)
        templateImgMatB, templateImgMatG, templateImgMatR = cv.split(templateImgMat)
        similarityB = match(targetImgMatB, templateImgMatB)
        similarityG = match(targetImgMatG, templateImgMatG)
        similarityR = match(targetImgMatR, templateImgMatR)
        similarity = (similarityB + similarityG + similarityR) / 3
        logger.debug(f"result of feature_matching is: <{similarity}>")
        return similarity

    @staticmethod
    def structure_similarity(targetImgMat, templateImgMat):
        """
        calculate the similarity of two images using structure comparison, images should be gray scale or colored
        shift of image pixel affects result a lot
        @param:
            targetImgMat: numpy.ndarray, matrix object of target image
            templateImgMat: numpy.ndarray, matrix object of template image
        @return:
            float: from 0 to 1, the structural similarity of two images
        """
        if targetImgMat.shape != templateImgMat.shape:
            logger.error(f"target image and template image must be in same shape: target shape={targetImgMat.shape}, template shape={templateImgMat.shape}")
            return 0
        if len(targetImgMat.shape) == 2:
            multi_channel = False
        elif len(targetImgMat.shape) == 3:
            multi_channel = True
        else:
            logger.error(f"target image shape<{targetImgMat.shape}> and template image shape<{templateImgMat.shape}> unsupported.")
            return 0

        result = metrics.structural_similarity(targetImgMat, templateImgMat, multichannel=multi_channel)
        logger.debug(f"structure similarity is: <{result}>")
        return result

    @staticmethod
    def edge(imageMat, alg: str = "canny", sigma: float = 1, **kwargs):
        """
        detect edges of images, mainly used for creating outline of images
        @param:
            imageMat: numpy.ndarray, matrix object of images, must be gray scale
            alg(optional): select algorithm from ["canny", "sobel", "scharr", "prewitt"]
            sigma(optional): float, parameter for filter, default to 1. available when alg = "canny"
        @return:
            tuple(matrix of True and False, matrix of gray level)
        """
        if alg.lower() == "sobel":
            edge = filters.sobel(imageMat)
        elif alg.lower() == "scharr":
            edge = filters.scharr(imageMat)
        elif alg.lower() == "prewitt":
            edge = filters.prewitt(imageMat)
        else:
            edge = feature.canny(imageMat, sigma=sigma, **kwargs)
            edge = numpy.where(edge == True, 255, 0)
            edge = edge.astype("uint8")

        return edge

    @staticmethod
    def detect_display(imageMat, resolution: (list, tuple)):
        """
        detect display's location
        @param:
            imageMat: matrix object of image
            resolution: resolution of real display, not camera resolution
        @return:
            (tuple, list): coordinates of top-left point and bottom-right point, (x1, y1, x2, y2)
        """
        # get image shape and gray scale
        height, width = imageMat.shape[:2]
        if len(imageMat.shape) == 3:
            imageMat = cv.cvtColor(imageMat, cv.COLOR_BGR2GRAY)

        # set threshold and get binary image
        kernel = numpy.ones((20, 20), numpy.uint8)
        open_img = cv.morphologyEx(imageMat, cv.MORPH_OPEN, kernel)
        ret, threshold_img = cv.threshold(open_img, 20, 255, cv.THRESH_BINARY)

        # image transform, find all possible rectangles
        kernel = numpy.ones((30, 30), numpy.uint8)
        edge_img1 = cv.morphologyEx(threshold_img, cv.MORPH_CLOSE, kernel)
        edge_img2 = cv.morphologyEx(edge_img1, cv.MORPH_OPEN, kernel)
        contours, hierarchy = cv.findContours(edge_img2, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

        # search for all rectangles
        display_location = []
        for contour in contours:
            # the area of current rectangle must be larger than 30 percent in original image
            area_pct = round(cv.contourArea(contour) / (height * width), 6)
            if area_pct < 0.3:
                continue
            # get rect(center point, size, rotation)
            rect = cv.minAreaRect(contour)
            h, w = rect[1]
            length_width_pct = (h / w) / (resolution[1] / resolution[0])
            if length_width_pct < 0.2 or length_width_pct > 3:
                continue
            # get coordinate of four points
            points = cv.boxPoints(rect)
            xs = sorted([int(x) for x in points[:, 0]])
            ys = sorted([int(x) for x in points[:, 1]])
            if xs[0] < 0 or xs[-1] > width:
                continue
            if ys[0] < 0 or ys[-1] > height:
                continue
            display_location.append([sum(xs[:2]) // 2, sum(ys[:2]) // 2, sum(xs[2:]) // 2, sum(ys[2:]) // 2])

        if len(display_location) <= 0:
            logger.warning(f"can not locate display, return full size")
            ret = 0, 0, width - 1, height - 1
        else:
            ret = display_location[0]
        return ret

    @staticmethod
    def resize_display(imageMat, resolution: (list, tuple), pt: (list, tuple) = None):
        """
        resize display, call self.detect_display first to detect location
        @param:
            imageMat: matrix object of image
            resolution: resolution of real display, not camera resolution
            pt: four integers as a list: [start x, start y, end x, end y]
        @return:
            matrix object of resized image
        """
        sx, sy, ex, ey = pt
        newImageMat = imageMat[sy:ey, sx:ex]
        resizedImageMat = cv.resize(newImageMat, resolution, interpolation=cv.INTER_AREA)

        return resizedImageMat

    def colored_match(self, targetImgMat, templateImgMat, threshold: float = 99):
        """
        check the color of image
        @param:
            targetImgMat: numpy.ndarray, matrix object of target image
            templateImgMat: numpy.ndarray, matrix object of template image
            threshold: the threshold for color similarity
        @return:
            bool: True if two images have the same color
                False if two images have different color
        """
        if not len(targetImgMat.shape) == len(templateImgMat.shape) == 3:
            logger.error(f"target image and template image must be colored image")
            return 0
        targetImgMatBin, templateImgMatBin, targetImgMatColor, templateImgMatColor = self.auto_resize(targetImgMat, templateImgMat, (200, 200))
        colorDiffCnt = 0
        for index1 in range(0, 200, 10):
            for index2 in range(0, 200, 10):
                tgBlock = targetImgMatColor[index1: index1 + 10, index2: index2 + 10]
                tpBlock = templateImgMatColor[index1: index1 + 10, index2: index2 + 10]
                tgColor = self.get_color(tgBlock, method=2, rmBackground=False)
                tpColor = self.get_color(tpBlock, method=2, rmBackground=False)
                if tgColor != tpColor:
                    colorDiffCnt += 1
        simi = 1 - round(colorDiffCnt / 400, 4)
        logger.info(f"color similarity of two images are: {simi}")
        return simi >= threshold

    @staticmethod
    def auto_resize(targetImgMat, templateImgMat, size: tuple = None, rmBackground: bool = False):
        """
        auto check image border and resize image based on the border
        @param:
            targetImgMat: numpy.ndarray, matrix object of target image
            templateImgMat: numpy.ndarray, matrix object of template image
            size: new size after resized, default to no resize
            rmBackground: remove background or not
        @return:
            tuple: (newTargetGrayImage, newTemplateGrayImage, newTargetColorImage, newTemplateColorImage)
        """
        targetImgMatColor = None
        templateImgMatColor = None
        if len(targetImgMat.shape) == len(templateImgMat.shape) == 3:
            targetImgMatColor = copy.deepcopy(targetImgMat)
            templateImgMatColor = copy.deepcopy(templateImgMat)

            targetImgMatGray = cv.cvtColor(targetImgMat, cv.COLOR_BGR2GRAY)
            templateImgMatGray = cv.cvtColor(templateImgMat, cv.COLOR_BGR2GRAY)
            ret1, targetImgMatBin = cv.threshold(targetImgMatGray, 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU)
            ret2, templateImgMatBin = cv.threshold(templateImgMatGray, 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU)
        elif len(targetImgMat.shape) == len(templateImgMat.shape) == 2:
            ret1, targetImgMatBin = cv.threshold(targetImgMat, 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU)
            ret2, templateImgMatBin = cv.threshold(templateImgMat, 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU)
        else:
            logger.error(f"target image and template image must be colored or gray scale at the same time")
            return None, None, None, None

        targetY, targetX = numpy.where(targetImgMatBin > 0)
        templateY, templateX = numpy.where(templateImgMatBin > 0)
        targetImgMatBin = targetImgMatBin[numpy.min(targetY): numpy.max(targetY), numpy.min(targetX): numpy.max(targetX)]
        templateImgMatBin = templateImgMatBin[numpy.min(templateY): numpy.max(templateY), numpy.min(templateX): numpy.max(templateX)]

        targetImgMatColor = targetImgMatColor[numpy.min(targetY): numpy.max(targetY), numpy.min(targetX): numpy.max(targetX)] if targetImgMatColor is not None else None
        templateImgMatColor = templateImgMatColor[numpy.min(templateY): numpy.max(templateY), numpy.min(templateX): numpy.max(templateX)] if templateImgMatColor is not None else None
        if rmBackground:
            targetImgMatColor = cv.bitwise_and(targetImgMatColor, targetImgMatColor, mask=targetImgMatBin) if targetImgMatColor is not None else None
            templateImgMatColor = cv.bitwise_and(templateImgMatColor, templateImgMatColor, mask=templateImgMatBin) if templateImgMatColor is not None else None

        if size and len(size) == 2:
            targetImgMatBin = cv.resize(targetImgMatBin, size, interpolation=cv.INTER_AREA)
            templateImgMatBin = cv.resize(templateImgMatBin, size, interpolation=cv.INTER_AREA)
            targetImgMatColor = cv.resize(targetImgMatColor, size, interpolation=cv.INTER_AREA)
            templateImgMatColor = cv.resize(templateImgMatColor, size, interpolation=cv.INTER_AREA)

        return targetImgMatBin, templateImgMatBin, targetImgMatColor, templateImgMatColor

    @staticmethod
    def get_color(imageMat, scope: (list, tuple) = None, method: int = 5, rmBackground: bool = True, threshold: int = 100):
        """
        get color names of image or image range
        @param:
            imageMat: matrix object of image, must be colored
            scope: four coordinates indicate a range or two coordinates indicate one point
            method: 0: get all colors and start coordinates and areas, return=[((0, 0), 'Black', 1931), ((25, 10), 'Blue', 539), ((4, 11), 'Cyan', 30)]
                    1: get all colors and areas, return=[('Black', 1931), ('Blue', 539), ('Cyan', 30)]
                    2: get main color of image, return= "Black"
                    3: get second color except main color, return= "Blue"
                    4: get main color except "Black", return="Blue"
                    5: get main color except "Black","Gray","White", return= "Blue"
            rmBackground: remove background or not
            threshold: threshold used for removing background, only available when rmBackground=True
        @return:
            str: name of color, yellow/red/black/white/green if length of scope is 2
            tuple: ((name of color, size of color), (name of color, size of color), ...)
        @example:
            print(obj.get_color())  # ["black", "yellow"]
            print(obj.get_color([10, 10]))  # ["red"]
            print(obj.get_color([10, 10, 50, 50]))  # ["yellow", "red", "white"]
        """
        if len(imageMat.shape) != 3:
            logger.error(f"image in gray scale could not retrieve color name")
            return None
        width, height = imageMat.shape[:2]
        if rmBackground:
            img_mask = copy.deepcopy(imageMat)
            img_mask = cv.cvtColor(img_mask, cv.COLOR_BGR2GRAY)
            ret, img_mask = cv.threshold(img_mask, threshold, 255, cv.THRESH_BINARY)
            imageMat = cv.bitwise_and(imageMat, imageMat, mask=img_mask)
        imageMat = cv.cvtColor(imageMat, cv.COLOR_BGR2HSV)
        if scope and all([isinstance(x, int) for x in scope]):
            if len(scope) == 2:
                x, y = scope
                if x < 0 or y < 0 or x >= width or y >= height:
                    logger.error(f"specified coordinate overflowed: <image shape={width}x{height}, coordinate={x}x{y}>")
                    return None
                H, S, V = imageMat[y, x]
                for c_name, c_value in COLOR.items():
                    if c_value["H"][0] <= H <= c_value["H"][1] and c_value['S'][0] <= S <= c_value["S"][1] and c_value["V"][0] <= V <= c_value["V"][1]:
                        return c_name if c_name not in ("Red1", "Red2") else "Red"
                logger.warning(f"could not match a color name with point: coordinate=<{x}, {y}>, BGR={B},{G},{R}")
                return None
            elif len(scope) == 4:
                x1, y1, x2, y2 = scope
                if x1 >= x2 or x1 < 0 or x2 < 0 or x1 >= width or x2 >= width:
                    logger.warning(f"specified scope overflowed: <image shape={width}x{height}, scope=({x1}, {y1}), ({x2}, {y2})>")
                elif y1 >= y2 or y1 < 0 or y2 < 0 or y1 >= height or y2 >= height:
                    logger.warning(f"specified scope overflowed: <image shape={width}x{height}, scope=({x1}, {y1}), ({x2}, {y2})>")
                else:
                    imageMat = imageMat[y1: y2, x1: x2]
                    width, height = imageMat.shape[:2]
        imgH, imgS, imgV = cv.split(imageMat)
        colors = COLOR.keys()
        color_area = []
        color_location_mat = numpy.zeros((width, height), numpy.uint8)
        for index, c in enumerate(colors):
            scopeH, scopeS, scopeV = COLOR[c]["H"], COLOR[c]["S"], COLOR[c]["V"]
            imgHT = numpy.where((imgH >= scopeH[0]) & (imgH <= scopeH[1]), 1, 0)
            imgST = numpy.where((imgS >= scopeS[0]) & (imgS <= scopeS[1]), 1, 0)
            imgVT = numpy.where((imgV >= scopeV[0]) & (imgV <= scopeV[1]), 1, 0)
            imgT = numpy.bitwise_and(imgHT, imgST)
            imgT = numpy.bitwise_and(imgT, imgVT)
            y, x = numpy.where(imgT > 0)
            if len(x) == 0:
                # color_area.append([None, c, 0])
                continue
            color_area.append([(x[0], y[0]), c, len(x)])
            color_location_mat[y[0], x[0]] = 1
        colored_area_sum = sum([x[-1] for x in color_area])
        if width * height - colored_area_sum > 0:
            color_area.append([None, "Other", width * height - colored_area_sum])
        pointY, pointX = numpy.where(color_location_mat > 0)
        points = list(zip(pointX, pointY))
        color_area_tmp = []
        for p in points:
            for loc, cn, area in color_area:
                if p == loc:
                    color_area_tmp.append((loc, cn, area))
                    break
        for loc, cn, area in color_area:
            if (loc, cn, area) not in color_area_tmp:
                color_area_tmp.append((loc, cn, area))
        red = []
        for index in range(len(color_area_tmp)):
            loc, cn, area = color_area_tmp[index]
            if cn in ("Red1", "Red2"):
                red.append([index, (loc, "Red", area)])
        if len(red) == 0:
            pass
        elif len(red) == 1:
            color_area_tmp = color_area_tmp[:red[0][0]] + red[0][1:] + color_area_tmp[red[0][0] + 1:]
        elif len(red) == 2:
            color_area_tmp = color_area_tmp[:red[0][0]] \
                             + [(red[0][1][0], "Red", red[0][1][2] + red[1][1][2])] \
                             + color_area_tmp[red[0][0] + 1: red[1][0]] \
                             + color_area_tmp[red[1][0] + 1:]

        logger.debug(f"color sequence of image: {color_area_tmp}")
        color_area_tmp_tmp = [x[1:] for x in color_area_tmp]
        color_area_tmp_tmp = sorted(color_area_tmp_tmp, key=lambda x: x[1], reverse=True)
        if method == 0:
            return color_area_tmp
        elif method == 1:
            return color_area_tmp_tmp
        elif method == 2:
            return color_area_tmp_tmp[0][0]
        elif method == 3:
            return color_area_tmp_tmp[1][0]
        elif method == 4:
            for cn, area in color_area_tmp_tmp:
                if cn != "Black":
                    return cn
        else:
            for cn, area in color_area_tmp_tmp:
                if cn not in ("Black", "Gray", "White"):
                    return cn

    @staticmethod
    def object_detect(imageMat, location: (tuple, list), factor: int = 4):
        """
        detect all possible locations of icon and return corresponding coordinate
        @param:
            imageMat: matrix object of image
            location: the location of template image, [100, 100, 150, 150]
            factor(optional): the factor for enlarging
        @return:
            list: a list of coordinates, [(0, 0, 100, 100), (10, 20, 110, 120), ...]
        """
        shape = imageMat.shape
        if len(shape) != 3:
            logger.error(f"image must be colored image, gray scale not supported")
            return
        height, width = shape[:2]
        sx, sy, ex, ey = location
        lx, ly = ex - sx, ey - sy
        sx = sx - (factor - 1) * lx // 2 if sx - (factor - 1) * lx // 2 >= 0 else 0
        sy = sy - (factor - 1) * ly // 2 if sy - (factor - 1) * ly // 2 >= 0 else 0
        ex = ex + (factor - 1) * lx // 2 if ex + (factor - 1) * lx // 2 <= width else width
        ey = ey + (factor - 1) * ly // 2 if ey + (factor - 1) * ly // 2 <= height else height

        newImageMat = imageMat[sy:ey, sx:ex]
        coordinates = []
        threshold = 10
        kernel_size = 2
        while threshold < 200:
            newImageGray = cv.cvtColor(newImageMat, cv.COLOR_BGR2GRAY)
            kernel = numpy.ones((kernel_size, kernel_size), numpy.uint8)
            open_img = cv.morphologyEx(newImageGray, cv.MORPH_CLOSE, kernel)
            ret, threshold_img = cv.threshold(open_img, threshold, 255, cv.THRESH_BINARY)
            contours, hierarchy = cv.findContours(threshold_img, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
            for contour in contours:
                # get rect(center point, size, rotation)
                rect = cv.minAreaRect(contour)
                # get coordinate of four points
                points = cv.boxPoints(rect)
                xs = sorted([int(x) for x in points[:, 0]])
                ys = sorted([int(x) for x in points[:, 1]])
                x1 = min(xs[:2]) if min(xs[:2]) >= 0 else 0
                y1 = min(ys[:2]) if min(ys[:2]) >= 0 else 0
                x2 = max(xs[2:]) if max(xs[2:]) <= ex - sx else ex - sx
                y2 = max(ys[2:]) if max(ys[2:]) <= ey - sy else ey - sy

                if x2 - x1 < 20 or y2 - y1 < 20:
                    continue
                if x2 - x1 > lx * 2 or y2 - y1 > ly * 2:
                    continue
                if x2 - x1 < lx / 2 or y2 - y1 < ly / 2:
                    continue
                nx1 = sx + int(x1 - (x2 - x1) * 0.05) if sx + int(x1 - (x2 - x1) * 0.05) >= 0 else 0
                ny1 = sy + int(y1 - (y2 - y1) * 0.05) if sy + int(y1 - (y2 - y1) * 0.05) >= 0 else 0
                nx2 = sx + int(x2 + (x2 - x1) * 0.05) if sx + int(x2 + (x2 - x1) * 0.05) <= width else width
                ny2 = sy + int(y2 + (y2 - y1) * 0.05) if sy + int(y2 + (y2 - y1) * 0.05) <= height else height

                if (nx1, ny1, nx2, ny2) not in coordinates:
                    coordinates.append((nx1, ny1, nx2, ny2))

            kernel_size += 2
            if kernel_size >= 20:
                kernel_size = 2
                threshold += 20

        return coordinates


if __name__ == "__main__":
    img1 = r"D:\Bruce\003_GIT\cluster_bak\ACT\output\camera\photo\record_2021_6_30-20_40_17_914061.png"
    image1 = cv.imdecode(numpy.fromfile(img1, dtype=numpy.uint8), cv.IMREAD_COLOR)
    print(ImageProcessing().object_detect(image1, location=[1550, 385, 1715, 477]))
