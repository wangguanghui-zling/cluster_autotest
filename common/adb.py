import subprocess
from datetime import datetime
from logger.logger import logger

class adb():
    """
    adb相关命令操作
    """
    @staticmethod
    def adb_root(devices:str):
        """
        导出安卓文件
        parame: devices: 设备地址通过adb devices获得
        """
        try:
            command = "adb -s {} root".format(devices)
            process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            process.stdin.close()
            process.wait()
            status_code=process.returncode  #执行状态码，为0表示执行成功，为1表示执行失败
            #cmd_result=process.communicate() #以元组的形式返回执行命令的输出
            logger.info("{}执行成功,执行状态码为{}".format(command,status_code))
        except Exception as e:
            logger.error(e)
            raise
        
    @staticmethod
    def adb_pull(devices:str,source:str,dest:str):
        """
        导出安卓文件
        parame: devices: 设备地址通过adb devices获得
        parame: source: 安卓路径
        parame: dest: 本地路径
        """
        try:
            command = "adb -s {} pull {} {}".format(devices,source,dest)
            process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            process.stdin.close()
            process.wait()
            status_code=process.returncode  #执行状态码，为0表示执行成功，为1表示执行失败
            #cmd_result=process.communicate() #以元组的形式返回执行命令的输出
            logger.info("{}执行成功,执行状态码为{}".format(command,status_code))
        except Exception as e:
            logger.error(e)
            raise
    @staticmethod
    def adb_pull_image(devices:str,source:str,dest:str,):
        """
        导出安卓下图片,主要用于导出仪表截图
        parame: devices: 设备地址通过adb devices获得
        parame: source: 安卓路径
        parame: dest: 本地路径
        return: dest_path: 返回截图存放路径
        """
        try:
            current_time = datetime.now()
            formatted_time = current_time.strftime("%Y%m%d-%H%M%S")
            dest_path = dest+'/'+ 'screenshot_'+ formatted_time+'.bmp'
            command = "adb -s {} pull {} {}".format(devices,source,dest_path)
            process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            process.stdin.close()
            process.wait()
            status_code=process.returncode  #执行状态码，为0表示执行成功，为1表示执行失败
            #cmd_result=process.communicate() #以元组的形式返回执行命令的输出
            logger.info("{}执行成功,执行状态码为{}".format(command,status_code))
            return dest_path
        except Exception as e:
            logger.error(e)
            raise
    @staticmethod
    def adb_devices():
        """
        获取adb设备
        return: devices: 返回设备名称
        """
        try:
            result = subprocess.run(['adb','devices'], stdout=subprocess.PIPE)
            output = result.stdout.decode('utf-8')
        except Exception as e:
            logger.error(e)
            raise