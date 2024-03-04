import serial


class ComReadWrite():
    """
    串口连接、读取、写入、断开
    """
    def __init__(self,comport,combaud):
        """
        parame: comport: 端口号
        parame: combaud: 波特率
        """
        self.port = serial.Serial(comport,combaud)

    def ComRead(self):
        """
        读取串口输出内容
        """
        while True:
            tmp = str(self.port.readline())
            line0 = ""
            if len(tmp) != 0:
                if r"\r\n'" in tmp:
                    line0 = tmp.split(r"\r\n'")[0]
                if r"b'" in line0:
                    line = line0.split(r"b'")[1]
                
    def ComToAdb(self):
        """
        开启adb
        """
        self.port.write("root\n".encode())
        self.port.write("telnet 192.168.118.1\n".encode())
        self.port.write("setprop persist.vendor.bosch.usb2.mode peripheral\n".encode())

    def ComToHost(self):
        """
        关闭adb
        """
        self.port.write("root\n".encode())
        self.port.write("telnet 192.168.118.1\n".encode())
        self.port.write("setprop persist.vendor.bosch.usb2.mode host\n".encode())

    def CloseCom(self):
        """
        关闭串口
        """
        self.port.close()

    def com_write(self,commend):
        """
        执行串口命令
        parame: commend: 端口命令
        """
        self.port.write(commend+"\n".encode('utf-8'))


test=ComReadWrite("COM34",115200)
test.com_write(b"/var/share/")
test.com_write(b"screenshot")