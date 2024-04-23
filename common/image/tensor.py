#! /usr/bin/env python



"""
machine learning library for image identification, most important API: predict
dependence:
    1. pip install tensorflow==2.6.0
"""

try:
    from common.logger.logger import logger
except (ImportError, ModuleNotFoundError):
    import logging as logger
import tensorflow
from tensorflow import keras
import numpy
import matplotlib.pyplot as plt
import os
import re
import random
import cv2 as cv
import time
import json


class Tensor:
    def __init__(
            self,
            train_data_path: str,
            model_path: str = None,
            project: str = None,
            train_pct: float = 90,
            model_name: str = "model.h5"
    ):
        """
        init tensorflow
        @param:
            train_data_path: absolute path of image data
            model_path: absolute path of trained model
            project(optional): project name, B02, B03, P05, etc
            train_pct(optional): percent for train image
            model_name(optional): model name
        """
        logger.debug(f"initialize tensorflow")
        self.__train_data_path = train_data_path
        self.__delete_images = []
        if model_path and os.path.exists(model_path):
            self.__model_path = model_path
        else:
            self.__model_path = os.path.split(os.path.abspath(__file__))[0]
        if not model_name.endswith(".h5"):
            logger.error(f"model name({model_name}) for tensorflow not allowed, must endswith '.h5'")
            raise NameError(f"model name({model_name}) for tensorflow not allowed, must endswith '.h5'")
        self.model = os.path.join(self.__model_path, model_name)
        self.__project = project
        self.__train_pct = train_pct
        self.__image_suffix = ".png"

        self.__train_paths = None
        self.__train_labels = None
        self.__test_paths = None
        self.__test_labels = None
        self.__label_index_map = None
        self.__index_label_map = None

        self.probability_model = None

    def predict(self, imageMat, threshold: float = 0.85):
        """
        predict the destination image and use the most credible result
        @param:
            imageMat: absolute path of image or image matrix in numpy format
            threshold: threshold for final predict result, from 0 to 1
        @return:
            tuple: (predicted icon name, predicted score)
        """
        if not os.path.exists(self.model):
            logger.info(f"generating tensorflow model for image predict")
            self.generate_model()
        if not self.probability_model:
            logger.info(f"loading tensorflow model from: {self.model}")
            model = tensorflow.keras.models.load_model(self.model)
            self.probability_model = tensorflow.keras.Sequential([model, tensorflow.keras.layers.Softmax()])
        if not self.__index_label_map and os.path.exists(self.model + ".json"):
            with open(self.model + ".json", 'r', encoding="utf-8") as mj:
                self.__index_label_map = json.load(mj)
                self.__index_label_map = {int(index): label for index, label in self.__index_label_map.items()}

        dst_image = self.load_images(imageMat)
        dst_image = (numpy.expand_dims(dst_image, 0))
        prediction = self.probability_model.predict(dst_image)
        # logger.debug(f"all predicted result: {prediction[0]}")

        max_value_index = numpy.argmax(prediction[0])
        max_icon_name = self.__index_label_map[max_value_index]
        logger.debug(f"the result of predicted image type: {max_icon_name} and similarity is: {prediction[0][max_value_index]}")

        if round(prediction[0][max_value_index], 4) >= threshold:
            return max_icon_name, round(prediction[0][max_value_index], 4)
        return None, 0

    def generate_model(self):
        """
        generate tensorflow model
        """
        self.collect_data_paths()
        train_images = numpy.array([self.load_images(p) for p in self.__train_paths])
        train_labels = numpy.array(self.__train_labels)
        test_images = numpy.array([self.load_images(p) for p in self.__test_paths])
        test_labels = numpy.array(self.__test_labels)

        model = keras.Sequential([
            keras.layers.Flatten(input_shape=(64, 64, 3)),
            keras.layers.Dense(128, activation='relu'),
            keras.layers.Dense(len(self.__index_label_map))
        ])
        model.compile(optimizer='adam',
                      loss=tensorflow.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
                      metrics=['accuracy'])
        model.fit(train_images, train_labels, epochs=10)
        model.save(self.model)
        logger.info(f"tensorflow model generated and saved as: {self.model}")

        test_loss, test_acc = model.evaluate(test_images, test_labels, verbose=2)
        logger.debug(f"the loss and accuracy for model are: <loss={test_loss}, accuracy={test_acc}>")

        self.delete_temp_images()

    def collect_data_paths(self):
        """
        collect image data and generate train images, train labels, test images, test labels
        """
        if not os.path.exists(self.__train_data_path):
            logger.error(f"train data path not found: {self.__train_data_path}")
            raise FileNotFoundError(f"train data path not found: {self.__train_data_path}")
        available_folders = []
        for dir_ in os.listdir(self.__train_data_path):
            groups = re.match(r".*?\((.*?)\)", dir_)
            if groups:
                projects = groups.group(1).split("+")
                if self.__project and self.__project not in projects:
                    logger.debug(f"'{dir_}' is not available for project '{self.__project}', skip")
                    continue
            available_folders.append(dir_)
            self.data_augment(os.path.join(self.__train_data_path, dir_))

        self.__label_index_map = {d: index for index, d in enumerate(available_folders)}
        self.__index_label_map = {index: d for d, index in self.__label_index_map.items()}
        logger.debug(f"mapping table for type and label: {self.__index_label_map}")
        with open(self.model + ".json", 'w', encoding="utf-8") as mj:
            json.dump(self.__index_label_map, mj, indent=4, ensure_ascii=False)
        all_image = {k: {"train": [], "test": []} for k in self.__label_index_map}
        for root, dirs, files in os.walk(self.__train_data_path):
            for f in files:
                current_dir = os.path.split(root)[1]
                if current_dir in available_folders:
                    all_image[current_dir]["train"].append((os.path.join(root, f), self.__label_index_map[current_dir]))
                else:
                    logger.warning(f"sub-folder: {current_dir} not supported, please move to the previous folder")

        for k in all_image:
            all_image[k]["test"] = all_image[k]["train"][int(len(all_image[k]["train"]) * self.__train_pct / 100):]
            all_image[k]["train"] = all_image[k]["train"][:int(len(all_image[k]["train"]) * self.__train_pct / 100)]

        train_set = [x for k, v in all_image.items() for x in v["train"]]
        test_set = [x for k, v in all_image.items() for x in v["test"]]
        random.shuffle(train_set)

        self.__train_paths = [x[0] for x in train_set]
        self.__train_labels = [x[1] for x in train_set]
        self.__test_paths = [x[0] for x in test_set]
        self.__test_labels = [x[1] for x in test_set]

    def load_images(self, image, resize: tuple = (64, 64)):
        """
        open and decode and normalize image data
        @param:
            image: absolute path of image or image matrix in numpy format
            resize(optional): destination size of all image data
        @return:
            tensorflow.Tensor: matrix of image in tensorflow format
        """
        if isinstance(image, str) and os.path.exists(image):
            imageMat = tensorflow.io.read_file(image)
            imageMat = tensorflow.image.decode_png(imageMat, channels=3)
        else:
            image = cv.cvtColor(image, cv.COLOR_BGR2RGB)
            imageMat = tensorflow.convert_to_tensor(image)
        imageMat = tensorflow.image.resize(imageMat, size=list(resize))
        imageMat /= 255.0

        return imageMat

    def data_augment(
            self,
            data_path: str,
            max_num: int = 100,
            random_scale: float = 0.2,
            random_rotation: float = 0.1,
            random_brightness: float = 0.1,
            random_contrast: tuple = (0.7, 1.3)
    ):
        """
        increase the image number of image, generate some images with random scale/rotation/brightness/contrast for each folder
        based on original images
        @param:
            data_path: absolute path of destination image folder
            max_num(optional): max image number
            random_scale(optional): generate a random scale factor from '1 - random_scale' to '1 + random_scale'
            random_rotation(optional): generate a random rotation factor from '-180 * random_rotation' to '180 * random_rotation'
            random_brightness(optional): generate a random brightness factor from '1 - random_brightness' to '1 + random_brightness'
            random_contrast(optional): generate a random contrast factor from 'random_contrast[0]' to 'random_contrast[1]'
        """
        logger.debug(f"generating more images for train data for folder: {data_path}")
        files = os.listdir(data_path)
        images = [x for x in files if x.endswith(self.__image_suffix)]
        if len(images) >= max_num:
            return
        for index in range(max_num - len(images)):
            image = os.path.join(data_path, images[index % len(images)])
            new_image = image[:-(len(self.__image_suffix))] + f"_tmp{index + 1}" + self.__image_suffix
            img = cv.imdecode(numpy.fromfile(image, dtype=numpy.uint8), cv.IMREAD_COLOR)

            # resize image randomly
            img = cv.resize(
                img,
                None,
                fx=round(random.uniform(1 - random_scale, 1 + random_scale), 2),
                fy=round(random.uniform(1 - random_scale, 1 + random_scale), 2),
                interpolation=cv.INTER_AREA
            ) if 0 < random_scale < 1 else img

            # rotation image randomly
            cx, cy = img.shape[1] // 2, img.shape[0] // 2
            degree = random.uniform(-180 * random_rotation, 180 * random_rotation)
            img = cv.warpAffine(
                img,
                cv.getRotationMatrix2D((cx, cy), degree, 1.0),
                (img.shape[1], img.shape[0])
            )

            # change image brightness randomly
            img = tensorflow.image.random_brightness(img, random_brightness)
            # change image contrast randomly
            img = tensorflow.image.random_contrast(img, random_contrast[0], random_contrast[1])
            img = img.numpy()

            cv.imencode('.png', img)[1].tofile(new_image)
            self.__delete_images.append(new_image)

    def delete_temp_images(self):
        """
        delete all generated images after tensorflow model has been generated and saved
        """
        if self.__delete_images:
            for p in self.__delete_images:
                if os.path.exists(p):
                    os.remove(p)
                    for _ in range(10):
                        if not os.path.exists(p):
                            break
                        time.sleep(0.1)


if __name__ == "__main__":
    ts = Tensor(r"D:\Bruce\003_GIT\cluster\ACT\resource\train", r"D:\Bruce\003_GIT\cluster\ACT\config")
    img_p = r"D:\Bruce\003_GIT\cluster_bak\ACT\resource\image\template\cap_Telltale_21.2.24\发动机水温高指示灯_ON(1809, 214, 1865, 261).png"
    img = cv.imdecode(numpy.fromfile(img_p, dtype=numpy.uint8), cv.IMREAD_COLOR)
    print(ts.predict(img_p))
