# coding: utf-8
"""API for setup/usage of Canoe COM Client interface.
"""
# --------------------------------------------------------------------------
# Standard library imports

import os
import time
from logger.logger import logger
from win32com.client import *
from win32com.client.connect import *

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


# Vector Canoe Class
class CANoe:
    """
    通过CANoe进行报文处理,需要接CANoe硬件
    """
    def __init__(self):
        """
        CANoe实例化,获取CANoe版本
        """
        try:
            self.application = None
            self.application = DispatchEx("CANoe.Application")
            self.ver = self.application.Version
            logger.info('Loaded CANoe version ',
                self.ver.major, '.',
                self.ver.minor, '.',
                self.ver.Build, '...')#, sep,''
            self.Measurement = self.application.Measurement.Running
            logger.info("CANoe初始化成功")
        except Exception as e:
            logger.error(e)
            raise

    def open_cfg(self, cfgname):
        # open CANoe simulation
        """
        打开CANoe工程
        parame: cfgname: CANoe工程路径
        """
        try:
            if (self.application != None):
                # check for valid file and it is *.cfg file
                if os.path.isfile(cfgname) and (os.path.splitext(cfgname)[1] == ".cfg"):
                    self.application.Open(cfgname)
                    logger.warning("opening..."+cfgname)
                else:
                    logger.error("没有找到CANoe工程文件,路径为{}".format(cfgname))
                    raise RuntimeError("Can't find CANoe cfg file")
            else:
                logger.error("CANoe应用程序丢失,无法打开模拟")
                raise RuntimeError("CANoe Application is missing,unable to open simulation")
        except Exception as e:
            logger.error(e)
            raise

    def close_cfg(self):
        # close CANoe simulation
        """
        关闭CANoe工程
        """
        try:
            if (self.application != None):
                logger.warning("close cfg ...")
                # self.stop_Measurement()
                self.application.Quit()
                self.application = None
        except Exception as e:
            logger.error(e)
            raise
        
    def start_Measurement(self):
        """
        启动CANoe测量
        """
        try:
            retry = 0
            retry_counter = 5
            # try to establish measurement within 5s timeout
            while not self.application.Measurement.Running and (retry < retry_counter):
                self.application.Measurement.Start()
                time.sleep(1)
                retry += 1
            if (retry == retry_counter):
                logger.error("CANoe启动测量失败,请检查连接")
                raise RuntimeWarning("CANoe start measuremet failed, Please Check Connection!")
            logger.info("成功启动测量")
        except Exception as e:
            logger.error(e)
            raise

    def stop_Measurement(self):
        """
        停止CANoe测量
        """
        try:
            if self.application.Measurement.Running:
                self.application.Measurement.Stop()
            else:
                pass
            logger.info("成功停止CANoe测量")
        except Exception as e:
            logger.error(e)
            raise

    def get_SigVal(self, channel_num, msg_name, sig_name, bus_type="CAN"):
        """
        通过CANoe接收信号
        param: channel_num: CAN通道
        param: msg_name: 报文名称
        param: sig_name: 信号名称
        param: bus_type: 总线类型CAN、LIN,默认为CAN
        exception: None
        """
        try:
            if (self.application != None):
                result = self.application.GetBus(bus_type).GetSignal(channel_num, msg_name, sig_name)
                logger.info("{}通道{}报文{}下的{}信号接收成功,收到的内容为{}".format(bus_type,channel_num, msg_name, sig_name,result.Value))
                return result.Value
            else:
                logger.error("CANoe未打开,无法获取变量")
                raise RuntimeError("CANoe is not open,unable to GetVariable")
        except Exception as e:
            logger.error(e)
            raise
    def set_SigVal(self, channel_num, msg_name, sig_name, bus_type,setValue):
        """
        通过CANoe发送信号
        param: channel_num: CAN通道
        param: msg_name: 报文名称
        param: sig_name: 信号名称
        param: bus_type: 总线类型CAN、LIN,默认为CAN
        exception: None
        """
        try:
            if (self.application != None):
                result = self.application.GetBus(bus_type).GetSignal(channel_num, msg_name, sig_name)
                result.Value = setValue
                logger.info("{}通道{}报文{}下的{}信号发送成功，发送的内容为{}".format(bus_type,channel_num, msg_name, sig_name,setValue))
            else:
                logger.error("CANoe未打开,无法获取变量")
                raise RuntimeError("CANoe is not open,unable to GetVariable")
        except Exception as e:
            logger.error(e)
            raise
    def DoEvents(self):
        """
        是一个用于处理 Windows 消息循环的函数。在某些情况下，当 Python
        与 COM 对象进行交互时，可能需要处理 Windows 消息循环，以确保程序的正常运行。
        会处理当前线程中的所有待处理的 Windows 消息。这对于一些 GUI 应用程序或者需
        要处理异步事件的场景非常有用，因为它可以确保程序在等待 COM 调用结果时，依然能够响应用户输入、更新界面等操作。
        """
        try:
            pythoncom.PumpWaitingMessages()
            time.sleep(1)
        except Exception as e:
            logger.error(e)
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