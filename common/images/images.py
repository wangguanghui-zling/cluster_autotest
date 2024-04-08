from PIL import Image, ImageChops
from common.logger.logger import logger
import pytesseract


class Images():
    """
    图片相关操作
    """
    def compare_by_matrix(self,expect_images:str,actal_images:str):
        """
        对比两张图片是否完全相同
        parame: expect_images: 图片地址
        parame: actal_images: 图片地址
        return: compare_result: 对比结果若为None则两张图片完全相同,若返回元组则两张图片存在差异
        """
        try:
            expect_image = Image.open(expect_images)
            actal_image = Image.open(actal_images)
            diff = ImageChops.difference(expect_image,actal_image)
            compare_result = diff.getbbox()
            logger.info("{}和{}两张图片对比结果为：{}".format(expect_images,actal_images,compare_result))
            return compare_result
        except Exception as e:
            logger.error(e)
            raise

    def compare_by_matrix_exclude(self,expect_images:str,actal_images:str,position:tuple):
        """
        对比两张图片指定位置以外区域是否完全相同,方法是将不需要区域设置成存白色,再进行对比
        parame: expect_images: 图片地址
        parame: actal_images: 图片地址
        parame: position: 不对比的区域start_x, start_y, end_x, end_y
        return: compare_result: 对比结果若为None则两张图片完全相同,若返回元组则两张图片存在差异
        """
        try:
            expect_image = Image.open(expect_images)
            actal_image = Image.open(actal_images)
            expect_images_exclude=self.set_area_to_white(expect_image,position)
            actal_images_exclude=self.set_area_to_white(actal_image,position)
            diff = ImageChops.difference(expect_images_exclude,actal_images_exclude)
            compare_result = diff.getbbox()
            logger.info("{}和{}两张图片指定区域{}以外的对比结果为{}".format(expect_images,actal_images,position,compare_result))
            return compare_result
        except Exception as e:
            logger.error(e)
            raise

    def compare_by_matrix_in_same_area(self,expect_images:str,actal_images:str,position:tuple):
        """
        对比两张图片指定区域是否完全相同
        parame: expect_images: 图片地址
        parame: actal_images: 图片地址
        parame: position: 对比的区域start_x, start_y, end_x, end_y
        return: compare_result: 对比结果若为None则两张图片完全相同,若返回元组则两张图片存在差异
        """
        try:
            expect_image = Image.open(expect_images)
            actal_image = Image.open(actal_images)
            expect_images_area=expect_image.crop(position)
            actal_images_area=actal_image.crop(position)
            diff = ImageChops.difference(expect_images_area,actal_images_area)
            compare_result = diff.getbbox()
            logger.info("{}和{}两张图片指定区域{}的对比结果为{}".format(expect_images,actal_images,position,compare_result))
            return compare_result
        except Exception as e:
            logger.error(e)
            raise

    def set_area_to_white(self,images:str,position:tuple):
        """
        将指定区域设置成白色
        parame: images: 图片地址
        parame: position: 设置成白色背景的区域start_x, start_y, end_x, end_y
        """
        try:
            image = Image.open(images)
            white_background = Image.new('RGB', image.size, (255, 255, 255))
            image.paste(white_background.crop(position), position)
            image.show()
            logger.info("{}图片指定区域{}成功设置为白色背景".format(images,position))
        except Exception as e:
            logger.error(e)
            raise
        
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
        try:
            image = Image.open(images)
            pytesseract.pytesseract.tesseract_cmd = tesseract_OCR #指定了 Tesseract OCR 引擎的安装路径
            text_string = pytesseract.image_to_string(image,lang='chi_sim')
            logger.info("{}图片文字识别成功文字内容为{},文字识别工具OCR路径为{}".format(images,text_string,tesseract_OCR))
            return text_string
        except Exception as e:
            logger.error(e)
            raise
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
        try:
            image = Image.open(images)
            area_images = image.crop(position)
            pytesseract.pytesseract.tesseract_cmd = tesseract_OCR #指定了 Tesseract OCR 引擎的安装路径
            text_string = pytesseract.image_to_string(area_images)
            logger.info("{}图片指定区域{}文字识别成功文字内容为{},文字识别工具OCR路径为{}".format(images,text_string,position,tesseract_OCR))
            return text_string
        except Exception as e:
            logger.error(e)
            raise
    
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
        try:
            image = Image.open(images)
            pytesseract.pytesseract.tesseract_cmd = tesseract_OCR #指定了 Tesseract OCR 引擎的安装路径
            boxes = pytesseract.image_to_boxes(content,output_type=pytesseract.Output.STRING)
            logger.info("{}图片文字识别成功文字内容为{},文字识别工具OCR路径为{}".format(images,boxes,tesseract_OCR))
        except Exception as e:
            logger.error(e)
            raise