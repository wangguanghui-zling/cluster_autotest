import win32com.client
import time

class CANoeoold():
    """
    自动调用设置好的CANoe工程,进行CAN报文的收发操作
    """
    def __init__(self,path:str,) -> None:
        """
        加载CANoe工程,设置CAN通道
        parame: path: CANoe工程路径
        parame: channel: CANoe通道
        """
        self.canoe = win32com.client.Dispatch("CANoe.Application") #创建CANoe.Application对象
        self.canoe.Open(path) #打开CANoe工程
        #self.channels = self.canoe.Channel(1) #设置CAN通道

    def loading_dbc(self,path:str):
        """
        加载DBC文件到通道
        parame: path: DBC路径
        """
        self.channels.SetDatabase(path) # 加载 DBC 文件到通道

    def start_measurement(self):
        """
        启动模拟
        """
        self.canoe.Measurement.Start() #启动测量
        #self.canoe.WaitUntilLoaded() #等待CANoe运行
    
    def transmit_message_dbc(self,messages,signals:str,values:float,cycle:float):
        """
        发送CAN报文,此方法只适用于有DBC
        parame: messages: 报文名,如果输入的是int则为报文ID,若是str则为报文名
        parame: signals: 信号名
        parame: values: 发送的值
        parame: cycle: 发送周期
        """
        if type(messages) == str:
            message = self.channel.Messages.Item(messages)
            signal = message.GetSignalByName(signals)
            signal.Value = values
            message.Send()
            time.sleep(cycle)

    def transmit_message_nodbc(self,id:int,value:list,dlc:int,cycle:float):
        """
        发送CAN报文,此方法只适用于无DBC
        parame: id: 报文id
        parame: values: 发送的值,十六进制数
        parame: cycle: 发送周期
        """

    def canoe_quit(self):
        """
        停止测试,并关闭CANoe工程
        """
        self.canoe.Quit() # 关闭 CANoe

# coding: utf-8
"""API for setup/usage of Canoe COM Client interface.
"""
# --------------------------------------------------------------------------
# Standard library imports
import os
import time
import msvcrt
from win32com.client import *
from win32com.client.connect import *

# Vector Canoe Class
class CANoe:
    def __init__(self):
        self.application = None
        self.application = DispatchEx("CANoe.Application")
        self.ver = self.application.Version
        print('Loaded CANoe version ',
            self.ver.major, '.',
            self.ver.minor, '.',
            self.ver.Build, '...')#, sep,''
        self.Measurement = self.application.Measurement.Running

    def open_cfg(self, cfgname):
        # open CANoe simulation
        if (self.application != None):
            # check for valid file and it is *.cfg file
            if os.path.isfile(cfgname) and (os.path.splitext(cfgname)[1] == ".cfg"):
                self.application.Open(cfgname)
                print("opening..."+cfgname)
            else:
                raise RuntimeError("Can't find CANoe cfg file")
        else:
            raise RuntimeError("CANoe Application is missing,unable to open simulation")

    def close_cfg(self):
        # close CANoe simulation
        if (self.application != None):
            print("close cfg ...")
            # self.stop_Measurement()
            self.application.Quit()
            self.application = None
    def start_Measurement(self):
        retry = 0
        retry_counter = 5
        # try to establish measurement within 5s timeout
        while not self.application.Measurement.Running and (retry < retry_counter):
            self.application.Measurement.Start()
            time.sleep(1)
            retry += 1
        if (retry == retry_counter):
            raise RuntimeWarning("CANoe start measuremet failed, Please Check Connection!")

    def stop_Measurement(self):
        if self.application.Measurement.Running:
            self.application.Measurement.Stop()
        else:
            pass
    def get_SigVal(self, channel_num, msg_name, sig_name, bus_type="CAN"):
        """
        @summary Get the value of a raw CAN signal on the CAN simulation bus
        @param channel_num - Integer value to indicate from which channel we will read the signal, usually start from 1,
                             Check with CANoe can channel setup.
        @param msg_name - String value that indicate the message name to which the signal belong. Check DBC setup.
        @param sig_name - String value of the signal to be read
        @param bus_type - String value of the bus type - e.g. "CAN", "LIN" and etc.
        @return The CAN signal value in floating point value.
                Even if the signal is of integer type, we will still return by
                floating point value.
        @exception None
        """
        if (self.application != None):
            result = self.application.GetBus(bus_type).GetSignal(channel_num, msg_name, sig_name)
            return result.Value
        else:
            raise RuntimeError("CANoe is not open,unable to GetVariable")
    def set_SigVal(self, channel_num, msg_name, sig_name, bus_type,setValue):
        if (self.application != None):
            result = self.application.GetBus(bus_type).GetSignal(channel_num, msg_name, sig_name)
            result.Value = setValue
        else:
            raise RuntimeError("CANoe is not open,unable to GetVariable")
    def DoEvents(self):
        pythoncom.PumpWaitingMessages()
        time.sleep(1)
"""
app = CANoe() #定义CANoe为app
app.open_cfg("E:/工作文档\学习文档/自动化/cluster_autotest/common/canoe_project/Configuration.cfg") #导入某个CANoe congif
time.sleep(5)
app.start_Measurement()
while not msvcrt.kbhit():
    #EngineSpeed = app.get_SigVal(channel_num=2, msg_name="GW_BCS_2_B", sig_name="BCS_VehSpd", bus_type="CAN")
    #print(EngineSpeed)
    app.set_SigVal(channel_num=2, msg_name="GW_BCS_2_B", sig_name="BCS_VehSpdVD", bus_type="CAN", setValue=1)
    app.DoEvents()
"""