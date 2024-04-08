from common.logger.logger import logger
import datetime
import time
import cv2
flag = True #控制开启录制结束录制的阀值,True开始录制,False结束录制

def duration(startTime:datetime, endTime:datetime):
    """
    计算两个时间点之间时长
    return: total_seconds: 返回时长,点位为秒
    """
    startTime2 = datetime.datetime.strptime(startTime, "%Y-%m-%d %H:%M:%S")
    endTime2 = datetime.datetime.strptime(endTime, "%Y-%m-%d %H:%M:%S")
    # 来获取时间差中的秒数。注意，seconds获得的秒只是时间差中的小时、分钟和秒部分的和，并没有包含时间差的天数（既是两个时间点不是同一天，失效）
    total_seconds = (endTime2 - startTime2).total_seconds()
    # 来获取准确的时间差，并将时间差转换为秒
    return total_seconds

class camera():
    """
    通过摄像头获取实时画面，并保存为视频
    """
    def __init__(self,index:int) -> None:
        try:
            """
            打开摄像头
            parame: index: 摄像头索引,当PC只有一个摄像头时设置成0,当PC有内置和外置两个摄像头时,0表示PC内置摄像头,1表示外置摄像头
            return: path: 保存的视频路径
            """
            self.capture = cv2.VideoCapture(index)
            logger.info("摄像头开启成功,摄像头索引为{}".format(index))
        except Exception as e:
            logger.error(e)
            raise

    def record_video_durat(self,path:str,fps:float,durat:int):
        """
        通过摄像头录制视频,录制指定时长
        parame: path:录制文件存放路径
        parame: fps:视频帧率
        parame: durat:录制时长,单位为秒
        return: file_path:返回录制视频路径
        """
        try:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # 使用MP4V编解码器
            file_name = time.strftime("%Y%m%d_%H%M%S", time.localtime())+".mp4"
            file_path = path+"\\"+file_name
            output = cv2.VideoWriter(file_path, fourcc, fps, (640, 480))  # 设置本地保存视频名称、格式、帧率、分辨率
            starttime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) #开始时间，用于计时
            while(self.capture.isOpened()):
                endtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                fenNum = duration(starttime, endtime) #计算时间间隔
                if fenNum<durat:
                    ret, frame = self.capture.read()
                    if ret==True:
                        output.write(frame) # 写入文件
                        if cv2.waitKey(1) & 0xFF == ord('q'): # 按下q键退出循环
                            break
                    else:
                        break
                else:
                    break
            logger.info("视频录制成功，视频保存路径为{}".format(file_name))
            return file_path
        except Exception as e:
            logger.error(e)
            raise
    def start_record_video(self,path:str,file:str,fps:float):
        """
        通过摄像头录制视频,录制指定时长
        parame: path:录制文件存放路径
        parame: file:文件名的前半部分,后半部分是以时间作为文件名的一部分
        parame: fps:视频帧率
        return: file_path:返回录制视频路径
        """
        try:
            global flag
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # 使用MP4V编解码器
            file_name = time.strftime("%Y%m%d_%H%M%S", time.localtime())+".mp4"
            file_path = path+"\\"+file+file_name
            output = cv2.VideoWriter(file_path, fourcc, fps, (640, 480))  # 设置本地保存视频名称、格式、帧率、分辨率
            while(self.capture.isOpened()):
                if flag==True:
                    ret, frame = self.capture.read()
                    if ret==True:
                        output.write(frame) # 写入文件
                        if cv2.waitKey(1) & 0xFF == ord('q'): # 按下q键退出循环
                            break
                    else:
                        break
                else:
                    break
            logger.info("视频录制成功，视频保存路径为{}".format(file_name))
            return file_path
        except Exception as e:
            logger.error(e)
            raise

    def show_camera(self):
        """
        显示摄像头实时界面
        """
        try:
            while(self.capture.isOpened()):
                ret, frame = self.capture.read()
                if ret==True:
                    cv2.imshow('Frame',frame) # 显示视频
                    if cv2.waitKey(1) & 0xFF == ord('q'):# 按下q键退出循环
                        break
                else:
                    break
        except Exception as e:
            logger.error(e)
            raise
