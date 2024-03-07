import subprocess
from datetime import datetime

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
        command = "adb -s {} root".format(devices)
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        process.stdin.close()
        process.wait()

    @staticmethod
    def adb_pull(devices:str,source:str,dest:str):
        """
        导出安卓文件
        parame: devices: 设备地址通过adb devices获得
        parame: source: 安卓路径
        parame: dest: 本地路径
        """
        command = "adb -s {} pull {} {}".format(devices,source,dest)
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        process.stdin.close()
        process.wait()
    @staticmethod
    def adb_pull_image(devices:str,source:str,dest:str,):
        """
        导出安卓下图片,主要用于导出仪表截图
        parame: devices: 设备地址通过adb devices获得
        parame: source: 安卓路径
        parame: dest: 本地路径
        return: dest_path: 返回截图存放路径
        """
        current_time = datetime.now()
        formatted_time = current_time.strftime("%Y%m%d-%H%M%S")
        dest_path = dest+'/'+ 'screenshot_'+ formatted_time+'.bmp'
        command = "adb -s {} pull {} {}".format(devices,source,dest_path)
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        process.stdin.close()
        process.wait()
        return dest_path
    @staticmethod
    def adb_devices():
        """
        获取adb设备
        return: devices: 返回设备名称
        """
        result = subprocess.run(['adb','devices'], stdout=subprocess.PIPE)
        output = result.stdout.decode('utf-8')