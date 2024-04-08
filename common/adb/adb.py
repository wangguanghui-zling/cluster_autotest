import subprocess
from datetime import datetime
from common.logger.logger import logger
import time

class adb():
    """
    adb相关命令操作
    """
    @staticmethod
    def adb_root(devices:str)-> None:
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
    def adb_pull(devices:str,source:str,dest:str)-> None:
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
    def adb_pull_image(devices:str,source:str,dest:str,)-> str:
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
    def adb_devices() -> None:
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

    @staticmethod
    def del_qnximage():
        """
        删除qnx仪表截图
        """
        try: #删除qnx路径下截图
            del_command = ("adb -s 192.168.7.16:5555 shell\n")
            proc = subprocess.Popen(del_command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            proc.stdin.write("busybox telnet 192.168.118.2\n"
                             "root\n"
                             "rm /var/share/screenshot.bmp\n")
            proc.stdin.flush()
            time.sleep(4)
            proc.stdin.close()
            proc.wait()
            status_code = proc.returncode  # 执行状态码，为0表示执行成功，为1表示执行失败
            logger.info("执行成功,执行状态码为{}".format(status_code))
        except Exception as e:
            logger.error(e)
            raise

    @staticmethod
    def del_iviimage():
        """
        删除android仪表截图
        """
        try: #删除android路径下截图
            del_command = ("adb -s 192.168.7.16:5555 shell\n")
            proc = subprocess.Popen(del_command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, text=True)
            proc.stdin.write("su\n"
                             "rm /data/nfs/nfs_share/screenshot.bmp\n"
                             "y\n")
            proc.stdin.flush()
            time.sleep(4)
            proc.stdin.close()
            proc.wait()
            status_code = proc.returncode  # 执行状态码，为0表示执行成功，为1表示执行失败
            logger.info("执行成功,执行状态码为{}".format(status_code))

        except Exception as e:
            logger.error(e)
            raise    