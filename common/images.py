from PIL import Image, ImageChops
import  pytesseract


class Images():
    """
    图片相关操作
    """
    def compare_by_matrix(self,expect_images:str,actal_images:str):
        """
        对比两张图片是否完全相同,这里注意当传入图片后就已经做了加载处理,所以不再需要调Image.open,否则会报错
        parame: expect_images: 图片地址
        parame: actal_images: 图片地址
        return: compare_result: 对比结果若为None则两张图片完全相同,若返回元组则两张图片存在差异
        """
        expect_images = Image.open(expect_images)
        actal_images = Image.open(actal_images)
        diff = ImageChops.difference(expect_images,actal_images)
        compare_result = diff.getbbox()
        return compare_result

    def compare_by_matrix_exclude(self,expect_images:str,actal_images:str,position:tuple):
        """
        对比两张图片指定位置以外区域是否完全相同,方法是将不需要区域设置成存白色,再进行对比
        这里注意当传入图片后就已经做了加载处理,所以不再需要调Image.open,否则会报错
        parame: expect_images: 图片地址
        parame: actal_images: 图片地址
        parame: position: 不对比的区域start_x, start_y, end_x, end_y
        return: compare_result: 对比结果若为None则两张图片完全相同,若返回元组则两张图片存在差异
        """
        expect_images = Image.open(expect_images)
        actal_images = Image.open(actal_images)
        expect_images_exclude=self.set_area_to_white(expect_images,position)
        actal_images_exclude=self.set_area_to_white(actal_images,position)
        diff = ImageChops.difference(expect_images_exclude,actal_images_exclude)
        compare_result = diff.getbbox()
        return compare_result

    def compare_by_matrix_in_same_area(self,expect_images:str,actal_images:str,position:tuple):
        """
        对比两张图片指定位置以外区域是否完全相同,这里注意当传入图片后就已经做了加载处理,所以不再需要调Image.open,否则会报错
        parame: expect_images: 图片地址
        parame: actal_images: 图片地址
        parame: position: 对比的区域start_x, start_y, end_x, end_y
        return: compare_result: 对比结果若为None则两张图片完全相同,若返回元组则两张图片存在差异
        """
        expect_images = Image.open(expect_images)
        actal_images = Image.open(actal_images)
        expect_images_area=expect_images.crop(position)
        actal_images_area=actal_images.crop(position)
        diff = ImageChops.difference(expect_images_area,actal_images_area)
        compare_result = diff.getbbox()
        return compare_result

    def set_area_to_white(self,images:str,position:tuple):
        """
        将指定区域设置成白色,这里注意当传入图片后就已经做了加载处理,所以不再需要调Image.open,否则会报错
        parame: images: 图片地址
        parame: position: 设置成白色背景的区域start_x, start_y, end_x, end_y
        """
        images = Image.open(images)
        white_background = Image.new('RGB', images.size, (255, 255, 255))
        images.paste(white_background.crop(position), position)
        
    def matrix_to_string(self,images:str,tesseract_OCR:str):
        """
        将图片内容转成文字,需要安装Tesseract OCR 引擎
        对于 macOS,您可以使用 Homebrew 安装:brew install tesseract
        对于 Windows,您可以从 https://github.com/UB-Mannheim/tesseract/wiki 下载安装程序并进行安装。
        对于 Linux,您可以使用包管理器安装,如 sudo apt-get install tesseract-ocr
        要识别中文还需要下中文语音包放到\ocr\tessdata目录下,下载地址:https://github.com/tesseract-ocr/tessdata/blob/main/chi_sim.traineddata
        parame: images: 图片地址
        parame: tesseract_OCR: OCR下的tesseract.exe地址
        return: text_string: 返回识别出来的文字
        """
        images = Image.open(images)
        pytesseract.pytesseract.tesseract_cmd = tesseract_OCR #指定了 Tesseract OCR 引擎的安装路径
        text_string = pytesseract.image_to_string(images,lang='chi_sim')
        return text_string
    def area_to_string(self,images:str,tesseract_OCR:str,position:tuple):
        """
        将图片指定区域文字转成文字
        对于 macOS,您可以使用 Homebrew 安装:brew install tesseract
        对于 Windows,您可以从 https://github.com/UB-Mannheim/tesseract/wiki 下载安装程序并进行安装。
        对于 Linux,您可以使用包管理器安装,如 sudo apt-get install tesseract-ocr
        parame: images: 图片地址
        parame: tesseract_OCR: OCR下的tesseract.exe地址
        parame: position: 需要识别的区域start_x, start_y, end_x, end_y
        """
        images = Image.open(images)
        area_images = images.crop(position)
        pytesseract.pytesseract.tesseract_cmd = tesseract_OCR #指定了 Tesseract OCR 引擎的安装路径
        text_string = pytesseract.image_to_string(area_images)
        return text_string
    
    def get_string_position(self,images:str,tesseract_OCR:str,content:str):#未完成
        """
        获取指定文字在图片中的位置
        对于 macOS,您可以使用 Homebrew 安装:brew install tesseract
        对于 Windows,您可以从 https://github.com/UB-Mannheim/tesseract/wiki 下载安装程序并进行安装。
        对于 Linux,您可以使用包管理器安装,如 sudo apt-get install tesseract-ocr
        parame: images: 图片地址
        parame: tesseract_OCR: OCR下的tesseract.exe地址
        parame: content: 想要识别的文字
        return: position: 返回文字所在的区域start_x, start_y, end_x, end_y
        """
        images = Image.open(images)
        pytesseract.pytesseract.tesseract_cmd = tesseract_OCR #指定了 Tesseract OCR 引擎的安装路径
        boxes = pytesseract.image_to_boxes(content,output_type=pytesseract.Output.STRING)
        print(boxes)

