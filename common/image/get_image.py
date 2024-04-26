import cv2
import tkinter as tk
from PIL import Image, ImageTk
import numpy as np
import threading
import os


class ImageCropper:
    def __init__(self, image_path):

        """
        Create a canvas to open the image and bind related operations
        @param:
		    image_path: The file path that needs to be opened
        """

        self.image = Image.open(image_path)
        self.crop_coordinates = None  # 用于存储裁剪区域的坐标

        self.root = tk.Tk()
        self.canvas_width = 1920  # 设置画布宽度
        self.canvas_height = 1080  # 设置画布高度
        self.canvas = tk.Canvas(self.root, width=self.canvas_width, height=self.canvas_height)
        self.canvas.pack()
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_release)

        self.photo = ImageTk.PhotoImage(self.image.resize((self.canvas_width, self.canvas_height)))  # 调整图片大小以适应画布
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)

        self.root.mainloop()  # 启动了 Tkinter 的事件循环，使窗口保持打开状态，直到用户关闭窗口。

    def on_mouse_press(self, event):
        """
        Used to record mouse press events
        """
        self.start_x = event.x
        self.start_y = event.y

    def on_mouse_drag(self, event):
        """
        Mouse drag event
        """
        self.canvas.delete("crop_rectangle")
        self.current_x = event.x
        self.current_y = event.y
        self.canvas.create_rectangle(self.start_x, self.start_y, self.current_x, self.current_y, outline="red",
                                     tags="crop_rectangle")

    def on_mouse_release(self, event):
        """
        Mouse Release Event
        """
        self.canvas.delete("crop_rectangle")
        self.end_x = event.x
        self.end_y = event.y
        self.crop_coordinates = (
            min(self.start_x, self.end_x), min(self.start_y, self.end_y), max(self.start_x, self.end_x),
            max(self.start_y, self.end_y))
        self.root.quit()

    def convert_coordinates(self, crop_coordinates, source_resolution, target_resolution):
        """
        Firstly, obtain the width and height of the source resolution and target resolution, calculate the horizontal
        and vertical scaling ratios, and then convert the coordinates of the cropping area from the source resolution to
        the target resolution based on the scaling ratio. Finally
        Returns the coordinates of the cropped area after conversion.
        """
        source_width, source_height = source_resolution
        target_width, target_height = target_resolution

        scale_x = target_width / source_width
        scale_y = target_height / source_height

        start_x, start_y, end_x, end_y = crop_coordinates
        start_x = int(start_x * scale_x)
        start_y = int(start_y * scale_y)
        end_x = int(end_x * scale_x)
        end_y = int(end_y * scale_y)

        return (start_x, start_y, end_x, end_y)

    def batch_crop_images(self, input_dir, output_dir, source_resolution, target_resolution):
        """
        Used for batch cropping images and creating output directories;
        Build input and output paths, then open the input image to convert the coordinates of the cropping area from
        source resolution to target resolution. Crop the image based on the converted coordinates, and finally save the
        cropped image to the output path,Generate cropped images named after coordinates
        """
        os.makedirs(output_dir, exist_ok=True)

        for filename in os.listdir(input_dir):
            if filename.endswith(".jpg") or filename.endswith(".png"):
                input_path = os.path.join(input_dir, filename)
                output_path = os.path.join(output_dir, str(self.crop_coordinates) + ".png")
                image = Image.open(input_path)
                converted_coordinates = self.convert_coordinates(self.crop_coordinates, source_resolution,
                                                                 target_resolution)
                cropped_image = image.crop(converted_coordinates)
                cropped_image.save(output_path)

                print(f"Cropped and saved image: {output_path}")


if __name__ == '__main__':
    # 图片路径
    image_path = r"E:\output1\photo\record_2024_4_25-14_40_10_621384.png"
    # 创建ImageCropper实例并获取裁剪区域坐标
    cropper = ImageCropper(image_path)
    crop_coordinates = cropper.crop_coordinates
    print("裁剪区域坐标:", crop_coordinates)
    print(type(crop_coordinates))
    input_dir = r"E:\output1\photo"
    output_dir = r"E:\output1"
    source_resolution = (1920, 1080)
    target_resolution = (1920, 1080)
    cropper.batch_crop_images(input_dir, output_dir, source_resolution, target_resolution)
