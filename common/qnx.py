import subprocess
import time

class qnx():
    """
    qnx相关命令操作,在安卓执行busybox telnet命令进入qnx,再执行qnx命令
    """
    def __init__(self,devices:str,ip:str,user:str,passwd:str):
        """
        #从安卓进入qnx
        parame: devices: 设备地址通过adb devices获得
        parame: ip: 目标ip地址,即qnx的ip地址
        parame: user: qnx登录账号
        parame: passwd: qnx登录密码     
        """
        command = "adb -s {} shell".format(devices)
        self.process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        time.sleep(1)
        self.process.stdin.write("busybox telnet {}\n".format(ip)) #从安卓进入qnx命令
        self.process.stdin.flush()
        time.sleep(1)
        self.process.stdin.write("{}\n".format(user)) #输入用户名
        self.process.stdin.flush()
        time.sleep(1)
        if passwd != "":
            self.process.stdin.write("{}\n".format(passwd)) #输入密码
            self.process.stdin.flush()
            time.sleep(1)
        
    def qnx_screenshot(self,save:str):
        """
        截取仪表界面图片
        parame: save: 图片保存路径即安卓与qnx的共享目录,注意不要保存到根目录或者系统路径很可能会报错
        """
        self.process.stdin.write("cd {}\n".format(save)) #输入密码
        self.process.stdin.flush()
        time.sleep(1)
        self.process.stdin.write("screenshot\n") #输入密码
        self.process.stdin.flush()
        time.sleep(1)
        self.process.stdin.close()
        self.process.wait()