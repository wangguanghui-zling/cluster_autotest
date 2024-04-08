# coding: utf-8
"""API for setup/usage of Canoe COM Client interface.
"""
# --------------------------------------------------------------------------
# Standard library imports
import os
import time
import cantools
import platform
from ctypes import *
from common.logger.logger import logger
from win32com.client import *
from win32com.client.connect import *

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
    
    def get_SysVar(self, ns_name, sysvar_name):
        """
        获取指定系统变量值
        param: ns_name: Namespace名称
        param: sysvar_name: 系统变量名
        return: result.Value: 系统变量值
        """
        try:
            if (self.application != None):
                systemCAN = self.application.System.Namespaces
                sys_namespace = systemCAN(ns_name)
                sys_value = sys_namespace.Variables(sysvar_name)
                logger.info("成功获取到{}空间下{}系统变量的值为{}".format(ns_name, sysvar_name, sys_value.Value))
                return sys_value.Value
            else:
                logger.error("CANoe未打开,无法获取变量")
                raise RuntimeError("CANoe is not open,unable to GetVariable")
        except Exception as e:
            logger.error(e)
            raise

    def set_SysVar(self, ns_name, sysvar_name, var):
        """
        设置指定系统变量值
        param: ns_name: Namespace名称即报文名
        param: sysvar_name: 系统变量名即信号名
        """
        try:
            if (self.application != None):
                systemCAN = self.application.System.Namespaces
                sys_namespace = systemCAN(ns_name)
                sys_value = sys_namespace.Variables(sysvar_name)
                sys_value.Value = var
                # print(sys_value)
                # result = sys_value(sys_name)
                #
                # result = var
                logger.info("{}空间下{}系统变量值成功设置为{}".format(ns_name, sysvar_name, var))
            else:
                logger.error("CANoe未打开,无法获取变量")
                raise RuntimeError("CANoe is not open,unable to GetVariable")
        except Exception as e:
            logger.error(e)
            raise

    def get_all_SysVar(self, ns_name):
        """
        获取所有变量信息
        return: sysvars: 以列表形式返回所有系统变量名和值
        """
        try:
            if (self.application != None):
                sysvars = []
                systemCAN = self.application.System.Namespaces
                sys_namespace = systemCAN(ns_name)
                sys_value = sys_namespace.Variables
                for sys in sys_value:
                    sysvars.append(sys.Name)
                    sysvars.append(sys.Value)
                logger.info("成功获取到所有系统变量，系统变量值为{}".format(sysvars))
                return sysvars
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

class DBC():
    """
    解析dbc文件,获取信号和报文内容,将信号的物理值转成原始值
    """
    def __init__(self,path) -> None:
        """
        加载DBC文件
        parame: path:dbc文件路径
        """
        self._bit_length = 8 #位长度
        self.db = cantools.database.load_file(path)

    def get_message_info(self,message:int)->dict:
        """
        通过报文id获取指定报文的name、dlc
        parame: message:报文ID,为十六进制数
        return: frame_dict:以字典形式返回报文的id、报文名称message、dlc
        """
        frame_dict = {"id":message,"message":"","dlc":""}
        frame_info = self.db.get_message_by_frame_id(message)
        frame_dict["message"]=frame_info.name #获取报文名称
        frame_dict["dlc"]=frame_info.length #获取报文DLC
        return frame_dict
    
    def get_signal_info(self,message:int,signal:str)->dict:
        """
        通过报文id获取指定报文的name、dlc
        parame: message:报文ID,为十六进制数
        parame: signal:信号名
        return: signal_dict:以字典形式返回信号的name信号名、start开始位、length长度、
        scale变换比例、offset偏移量,报文的id、报文名称message、dlc
        """
        signal_dict = {
                        "id":hex(message),
                        "message":"",
                        "dlc":"",
                        "name":signal,
                        "start":"",
                        "length":"",
                        "scale":"",
                        "offset":""
                        }
        frame_info = self.db.get_message_by_frame_id(message)
        signal_dict["message"]=frame_info.name #获取报文名称
        signal_dict["dlc"]=frame_info.length #获取报文DLC
        signal_info = frame_info.get_signal_by_name(signal)
        signal_dict["start"]=signal_info.start #获取信号开始位
        signal_dict["length"]=signal_info.length #获取信号长度
        signal_dict["scale"]=signal_info.scale #获取变换比例
        signal_dict["offset"]=signal_info.offset #获取变换比例
        return signal_dict

    def physical_to_raw(self,message:int,signal:str,physical:int):
        """
        将对应信号的物理值转成原始值,公式为: 原始值 = (物理值 - 偏移量) / 缩放因子,其中缩放因子也叫变换比例
        parame: message:报文ID,为十六进制数
        parame: signal:信号名称
        parame: physical:物理值
        return: value:返回原始值,为十进制数
        """
        signal_dict=self.get_signal_info(message,signal)
        value = int((physical-signal_dict["offset"])/signal_dict["scale"])
        return value
    
    def completion_byte(self,byte_value: str, size: int = 8) -> str:
        """
        如果不足size位,补齐size位
        parame: byte_value:需要补齐指定长度的字符串
        parame: size:长度
        return: byte_value: 返回8位的字符串
        """
        # 补齐8位
        while len(byte_value) != size:
            byte_value = "0" + byte_value
        return byte_value

    def get_byte_bit(self,start_bit:int,length:int,)-> tuple:
        """
        获取信号在报文原始帧中,占几个byte,从第几个byte开始,在第几个bit开始
        parame: start_bit:信号的开始位
        parame: length:信号长度
        return: signal_info_dict:返回字典其中各个字段含义如下:
        byte_position:从第几个byte开始
        bit_position:从第几个bit开始
        byte_len:占用几个byte
        """
        signal_info_dict={
                        'byte_position':'',
                        'bit_position':'',
                        'byte_len':''
                        }
        signal_info_dict["byte_position"] = (start_bit // self._bit_length)+1 #在哪个byte位开始
        signal_info_dict["bit_position"] = (start_bit % self._bit_length)+1 #在哪个bit位开始
        signal_info_dict["byte_len"] = (length // self._bit_length)+1 #占用几个byte
        return signal_info_dict

    def split_bytes(self,value:int,start_bit:int,byte_len:int)->list:
        """
        根据start_bit将十六进制数拆分成多个byte,再以列表返回
        parame: value:十进制数,信号的原始值
        parame: start_bit:信号在首个byte上的第几个bit开始
        parame: byte_len:信号占用几个byte
        return: values_list:以列表形式返回多个byte值
        """
        values_list = [] #用于存储已转成一个个的byte数字
        value_bin_str = str(bin(value)[2:]) #将十六进制数转出二进制去掉前两位后再转出字符串
        if byte_len > 1:
            value_bin_str_byte=value_bin_str[:self._bit_length-start_bit] #截取出第一个byte里的数据
            value_hex=hex(int(value_bin_str_byte, 2)) #将字符串转成二进制后再转成十六进制
            values_list.append(value_hex)#获取剩余未转成16进制的字符串
            surplus_bit=value_bin_str[self._bit_length-start_bit:]
            for i in range(0,len(surplus_bit),8):#将剩余字符按长度为8分开后转成16进制存到列表中
                byte_str=surplus_bit[i:i+8]
                byte_hex=hex(int(byte_str, 2))
                values_list.append(byte_hex)
        else:
            value_bit_str = value_bin_str + (start_bit-1)*'0'
            value_hex=hex(int(value_bit_str, 2))
            values_list.append(value_hex)
        return values_list

    def set_message_frame(self,datas:list,start_byte:int,values:list,byte_len:int)->list:
        """
        用于设置Signal后,计算出8Byte的值
        parame: datas:帧的默认值为[0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00]
        parame: start_byte:信号从第几个byte开始
        parame: values:对应信号已转成byte后的列表
        parame: byte_len:信号占用几个byte
        return: datas:以列表形式返回计算出8Byte的值
        """
        n=0
        for i in range(len(datas)):
            if start_byte<=i<=(start_byte+byte_len-1):
                if datas[i] != 0:#当多个信号占用一个byte是需要将值转成十进制相加后，再存到对应byte
                    if type(datas[i]) == str:
                        datas[i]=int(datas[i],16)
                    if type(values[n]) == str:
                       values[n] = int(values[n],16)
                    datas[i]=datas[i]+values[n]
                else:
                    if type(values[n]) != int:
                        datas[i]=int(values[n],16)
                    else:
                        datas[i]=values[n]
                n=n+1
        for j in range(len(datas)):
            if type(datas[j]) != int:
                datas[j] = int(datas[j], 16)
        return datas

def physical_to_frame(dbc_path,byte_data,message_id,signal_name,signal_value):
    """
    将指定报id的用指定信号设置为指定值后,计算出8Byte的值
    parame: dbc_path:dbc文件路径
    parame: byte_data:帧的默认值为[0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00]
    parame: message_id:报文id
    parame: signal_name:信号名
    parame: signal_value:对应信号发送的值(物理值)
    return: message_frame:以列表形式返回计算出8Byte的值
    """
    try:
        dbc_data = DBC(dbc_path)
        signal_info =  dbc_data.get_signal_info(message_id,signal_name)
        signal_value = dbc_data.physical_to_raw(message_id,signal_name,signal_value)
        signal_value_byte=dbc_data.get_byte_bit(signal_info['start'],signal_info['length'])
        signal_byte=dbc_data.split_bytes(signal_value,signal_value_byte['bit_position'],signal_value_byte["byte_len"])
        message_frame = dbc_data.set_message_frame(byte_data,signal_value_byte['byte_position'],signal_byte,signal_value_byte['byte_len'])
        return message_frame
    except Exception as e:
        logger.error(e)
        raise

###############################################################################
"""
USBCAN收发报文
1、使用zlgcan进行二次开发, 依赖 Microsoft Visual C++运行库版本（必须具备）： 2005、2008、2010、2012、2013, 所以下载安装 VS运行库
2、x86只能用x86的kerneldlls和zlgcan.dll文件,64只能用64的kerneldlls和zlgcan.dll文件
"""

ZCAN_DEVICE_TYPE = c_uint

INVALID_DEVICE_HANDLE  = 0
INVALID_CHANNEL_HANDLE = 0

'''
 Device Type
'''
ZCAN_PCI5121          = ZCAN_DEVICE_TYPE(1) 
ZCAN_PCI9810          = ZCAN_DEVICE_TYPE(2) 
ZCAN_USBCAN1          = ZCAN_DEVICE_TYPE(3) 
ZCAN_USBCAN2          = ZCAN_DEVICE_TYPE(4) 
ZCAN_PCI9820          = ZCAN_DEVICE_TYPE(5) 
ZCAN_CAN232           = ZCAN_DEVICE_TYPE(6) 
ZCAN_PCI5110          = ZCAN_DEVICE_TYPE(7) 
ZCAN_CANLITE          = ZCAN_DEVICE_TYPE(8) 
ZCAN_ISA9620          = ZCAN_DEVICE_TYPE(9) 
ZCAN_ISA5420          = ZCAN_DEVICE_TYPE(10)
ZCAN_PC104CAN         = ZCAN_DEVICE_TYPE(11)
ZCAN_CANETUDP         = ZCAN_DEVICE_TYPE(12)
ZCAN_CANETE           = ZCAN_DEVICE_TYPE(12)
ZCAN_DNP9810          = ZCAN_DEVICE_TYPE(13)
ZCAN_PCI9840          = ZCAN_DEVICE_TYPE(14)
ZCAN_PC104CAN2        = ZCAN_DEVICE_TYPE(15)
ZCAN_PCI9820I         = ZCAN_DEVICE_TYPE(16)
ZCAN_CANETTCP         = ZCAN_DEVICE_TYPE(17)
ZCAN_PCIE_9220        = ZCAN_DEVICE_TYPE(18)
ZCAN_PCI5010U         = ZCAN_DEVICE_TYPE(19)
ZCAN_USBCAN_E_U       = ZCAN_DEVICE_TYPE(20)
ZCAN_USBCAN_2E_U      = ZCAN_DEVICE_TYPE(21)
ZCAN_PCI5020U         = ZCAN_DEVICE_TYPE(22)
ZCAN_EG20T_CAN        = ZCAN_DEVICE_TYPE(23)
ZCAN_PCIE9221         = ZCAN_DEVICE_TYPE(24)
ZCAN_WIFICAN_TCP      = ZCAN_DEVICE_TYPE(25)
ZCAN_WIFICAN_UDP      = ZCAN_DEVICE_TYPE(26)
ZCAN_PCIe9120         = ZCAN_DEVICE_TYPE(27)
ZCAN_PCIe9110         = ZCAN_DEVICE_TYPE(28)
ZCAN_PCIe9140         = ZCAN_DEVICE_TYPE(29)
ZCAN_USBCAN_4E_U      = ZCAN_DEVICE_TYPE(31)
ZCAN_CANDTU_200UR     = ZCAN_DEVICE_TYPE(32)
ZCAN_CANDTU_MINI      = ZCAN_DEVICE_TYPE(33)
ZCAN_USBCAN_8E_U      = ZCAN_DEVICE_TYPE(34)
ZCAN_CANREPLAY        = ZCAN_DEVICE_TYPE(35)
ZCAN_CANDTU_NET       = ZCAN_DEVICE_TYPE(36)
ZCAN_CANDTU_100UR     = ZCAN_DEVICE_TYPE(37)
ZCAN_PCIE_CANFD_100U  = ZCAN_DEVICE_TYPE(38)
ZCAN_PCIE_CANFD_200U  = ZCAN_DEVICE_TYPE(39)
ZCAN_PCIE_CANFD_400U  = ZCAN_DEVICE_TYPE(40)
ZCAN_USBCANFD_200U    = ZCAN_DEVICE_TYPE(41)
ZCAN_USBCANFD_100U    = ZCAN_DEVICE_TYPE(42)
ZCAN_USBCANFD_MINI    = ZCAN_DEVICE_TYPE(43)
ZCAN_CANFDCOM_100IE   = ZCAN_DEVICE_TYPE(44)
ZCAN_CANSCOPE         = ZCAN_DEVICE_TYPE(45)
ZCAN_CLOUD            = ZCAN_DEVICE_TYPE(46)
ZCAN_CANDTU_NET_400   = ZCAN_DEVICE_TYPE(47)
ZCAN_CANFDNET_200U_TCP     = ZCAN_DEVICE_TYPE(48)
ZCAN_CANFDNET_200U_UDP     = ZCAN_DEVICE_TYPE(49)
ZCAN_CANFDWIFI_100U_TCP    = ZCAN_DEVICE_TYPE(50)
ZCAN_CANFDWIFI_100U_UDP    = ZCAN_DEVICE_TYPE(51)
ZCAN_CANFDNET_400U_TCP     = ZCAN_DEVICE_TYPE(52)
ZCAN_CANFDNET_400U_UDP     = ZCAN_DEVICE_TYPE(53)
ZCAN_CANFDBLUE_200U        = ZCAN_DEVICE_TYPE(54)
ZCAN_CANFDNET_100U_TCP     = ZCAN_DEVICE_TYPE(55)
ZCAN_CANFDNET_100U_UDP     = ZCAN_DEVICE_TYPE(56)
ZCAN_CANFDNET_800U_TCP     = ZCAN_DEVICE_TYPE(57)
ZCAN_CANFDNET_800U_UDP     = ZCAN_DEVICE_TYPE(58)
ZCAN_USBCANFD_800U         = ZCAN_DEVICE_TYPE(59)
ZCAN_PCIE_CANFD_100U_EX     = ZCAN_DEVICE_TYPE(60)
ZCAN_PCIE_CANFD_400U_EX     = ZCAN_DEVICE_TYPE(61)
ZCAN_PCIE_CANFD_200U_MINI   = ZCAN_DEVICE_TYPE(62)
ZCAN_PCIE_CANFD_200U_M2     = ZCAN_DEVICE_TYPE(63)
ZCAN_PCIE_CANFD_200U_EX     = ZCAN_DEVICE_TYPE(62)
ZCAN_CANFDDTU_400_TCP       = ZCAN_DEVICE_TYPE(64)
ZCAN_CANFDDTU_400_UDP       = ZCAN_DEVICE_TYPE(65)
ZCAN_CANFDWIFI_200U_TCP     = ZCAN_DEVICE_TYPE(66)
ZCAN_CANFDWIFI_200U_UDP     = ZCAN_DEVICE_TYPE(67)
ZCAN_CANFDDTU_800ER_TCP     = ZCAN_DEVICE_TYPE(68)
ZCAN_CANFDDTU_800ER_UDP     = ZCAN_DEVICE_TYPE(69)
ZCAN_CANFDDTU_800EWGR_TCP   = ZCAN_DEVICE_TYPE(70)
ZCAN_CANFDDTU_800EWGR_UDP   = ZCAN_DEVICE_TYPE(71)
ZCAN_CANFDDTU_600EWGR_TCP   = ZCAN_DEVICE_TYPE(72)
ZCAN_CANFDDTU_600EWGR_UDP   = ZCAN_DEVICE_TYPE(73)
ZCAN_VIRTUAL_DEVICE         = ZCAN_DEVICE_TYPE(99)

'''
 Interface return status
'''
ZCAN_STATUS_ERR         = 0
ZCAN_STATUS_OK          = 1
ZCAN_STATUS_ONLINE      = 2
ZCAN_STATUS_OFFLINE     = 3
ZCAN_STATUS_UNSUPPORTED = 4

'''
 CAN type
'''
ZCAN_TYPE_CAN    = c_uint(0)
ZCAN_TYPE_CANFD  = c_uint(1)

def input_thread():
   input()


'''
 Device information
'''
class ZCAN_DEVICE_INFO(Structure):
    _fields_ = [("hw_Version", c_ushort),
                ("fw_Version", c_ushort),
                ("dr_Version", c_ushort), 
                ("in_Version", c_ushort), 
                ("irq_Num", c_ushort),
                ("can_Num", c_ubyte),
                ("str_Serial_Num", c_ubyte * 20),
                ("str_hw_Type", c_ubyte * 40),
                ("reserved", c_ushort * 4)]

    def __str__(self):
        return "Hardware Version:%s\nFirmware Version:%s\nDriver Interface:%s\nInterface Interface:%s\nInterrupt Number:%d\nCAN Number:%d\nSerial:%s\nHardware Type:%s\n" %( \
                self.hw_version, self.fw_version, self.dr_version, self.in_version, self.irq_num, self.can_num, self.serial, self.hw_type)
                
    def _version(self, version):
        return ("V%02x.%02x" if version // 0xFF >= 9 else "V%d.%02x") % (version // 0xFF, version & 0xFF)
    
    @property
    def hw_version(self):
        return self._version(self.hw_Version)

    @property
    def fw_version(self):
        return self._version(self.fw_Version)
    
    @property
    def dr_version(self):
        return self._version(self.dr_Version)
    
    @property
    def in_version(self):
        return self._version(self.in_Version)

    @property
    def irq_num(self):
        return self.irq_Num

    @property
    def can_num(self):
        return self.can_Num

    @property
    def serial(self):
        serial = ''
        for c in self.str_Serial_Num:
            if c > 0: 
               serial += chr(c)
            else:
                break 
        return serial

    @property
    def hw_type(self):
        hw_type = ''
        for c in self.str_hw_Type:
            if c > 0:
                hw_type += chr(c)
            else:
                break
        return hw_type

class _ZCAN_CHANNEL_CAN_INIT_CONFIG(Structure):
    _fields_ = [("acc_code", c_uint),
                ("acc_mask", c_uint),
                ("reserved", c_uint),
                ("filter",   c_ubyte),
                ("timing0",  c_ubyte),
                ("timing1",  c_ubyte),
                ("mode",     c_ubyte)]

class _ZCAN_CHANNEL_CANFD_INIT_CONFIG(Structure):
    _fields_ = [("acc_code",     c_uint),
                ("acc_mask",     c_uint),
                ("abit_timing",  c_uint),
                ("dbit_timing",  c_uint),
                ("brp",          c_uint),
                ("filter",       c_ubyte),
                ("mode",         c_ubyte),
                ("pad",          c_ushort),
                ("reserved",     c_uint)]

class _ZCAN_CHANNEL_INIT_CONFIG(Union):
    _fields_ = [("can", _ZCAN_CHANNEL_CAN_INIT_CONFIG), ("canfd", _ZCAN_CHANNEL_CANFD_INIT_CONFIG)]

class ZCAN_CHANNEL_INIT_CONFIG(Structure):
    _fields_ = [("can_type", c_uint),
                ("config", _ZCAN_CHANNEL_INIT_CONFIG)]

class ZCAN_CHANNEL_ERR_INFO(Structure):
    _fields_ = [("error_code", c_uint),
                ("passive_ErrData", c_ubyte * 3),
                ("arLost_ErrData", c_ubyte)]

class ZCAN_CHANNEL_STATUS(Structure):
    _fields_ = [("errInterrupt", c_ubyte),
                ("regMode",      c_ubyte),
                ("regStatus",    c_ubyte), 
                ("regALCapture", c_ubyte),
                ("regECCapture", c_ubyte),
                ("regEWLimit",   c_ubyte),
                ("regRECounter", c_ubyte),
                ("regTECounter", c_ubyte),
                ("Reserved",     c_ubyte)]

class ZCAN_CAN_FRAME(Structure):
    _fields_ = [("can_id",  c_uint, 29),
                ("err",     c_uint, 1),
                ("rtr",     c_uint, 1),
                ("eff",     c_uint, 1), 
                ("can_dlc", c_ubyte),
                ("__pad",   c_ubyte),
                ("__res0",  c_ubyte),
                ("__res1",  c_ubyte),
                ("data",    c_ubyte * 8)]

class ZCAN_CANFD_FRAME(Structure):
    _fields_ = [("can_id", c_uint, 29), 
                ("err",    c_uint, 1),
                ("rtr",    c_uint, 1),
                ("eff",    c_uint, 1), 
                ("len",    c_ubyte),
                ("brs",    c_ubyte, 1),
                ("esi",    c_ubyte, 1),
                ("__pad",  c_ubyte, 6),
                ("__res0", c_ubyte),
                ("__res1", c_ubyte),
                ("data",   c_ubyte * 64)]

class ZCAN_Transmit_Data(Structure):
    _fields_ = [("frame", ZCAN_CAN_FRAME), ("transmit_type", c_uint)]

class ZCAN_Receive_Data(Structure):
    _fields_  = [("frame", ZCAN_CAN_FRAME), ("timestamp", c_ulonglong)]

class ZCAN_TransmitFD_Data(Structure):
    _fields_ = [("frame", ZCAN_CANFD_FRAME), ("transmit_type", c_uint)]

class ZCAN_ReceiveFD_Data(Structure):
    _fields_ = [("frame", ZCAN_CANFD_FRAME), ("timestamp", c_ulonglong)]

class ZCAN_AUTO_TRANSMIT_OBJ(Structure):
    _fields_ = [("enable",   c_ushort),
                ("index",    c_ushort),
                ("interval", c_uint),
                ("obj",      ZCAN_Transmit_Data)]

class ZCANFD_AUTO_TRANSMIT_OBJ(Structure):
    _fields_ = [("enable",   c_ushort),
                ("index",    c_ushort),
                ("interval", c_uint),
                ("obj",      ZCAN_TransmitFD_Data)]

class ZCANFD_AUTO_TRANSMIT_OBJ_PARAM(Structure):   #auto_send delay
    _fields_ = [("indix",  c_ushort),
                ("type",   c_ushort),
                ("value",  c_uint)]

class IProperty(Structure):
    _fields_ = [("SetValue", c_void_p), 
                ("GetValue", c_void_p),
                ("GetPropertys", c_void_p)]

class ZCAN(object):
    def __init__(self):
        if platform.system() == "Windows":
            self.__dll = windll.LoadLibrary("common/can/hardware/zlgcan.dll")
        else:
            print("No support now!")
        if self.__dll == None:
            print("DLL couldn't be loaded!")

    def OpenDevice(self, device_type, device_index, reserved):
        try:
            return self.__dll.ZCAN_OpenDevice(device_type, device_index, reserved)
        except:
            print("Exception on OpenDevice!") 
            raise

    def CloseDevice(self, device_handle):
        try:
            return self.__dll.ZCAN_CloseDevice(device_handle)
        except:
            print("Exception on CloseDevice!")
            raise

    def GetDeviceInf(self, device_handle):
        try:
            info = ZCAN_DEVICE_INFO()
            ret = self.__dll.ZCAN_GetDeviceInf(device_handle, byref(info))
            return info if ret == ZCAN_STATUS_OK else None
        except:
            print("Exception on ZCAN_GetDeviceInf")
            raise

    def DeviceOnLine(self, device_handle):
        try:
            return self.__dll.ZCAN_IsDeviceOnLine(device_handle)
        except:
            print("Exception on ZCAN_ZCAN_IsDeviceOnLine!")
            raise

    def InitCAN(self, device_handle, can_index, init_config):
        try:
            return self.__dll.ZCAN_InitCAN(device_handle, can_index, byref(init_config))
        except:
            print("Exception on ZCAN_InitCAN!")
            raise

    def StartCAN(self, chn_handle):
        try:
            return self.__dll.ZCAN_StartCAN(chn_handle)
        except:
            print("Exception on ZCAN_StartCAN!")
            raise

    def ResetCAN(self, chn_handle):
        try:
            return self.__dll.ZCAN_ResetCAN(chn_handle)
        except:
            print("Exception on ZCAN_ResetCAN!")
            raise

    def ClearBuffer(self, chn_handle):
        try:
            return self.__dll.ZCAN_ClearBuffer(chn_handle)
        except:
            print("Exception on ZCAN_ClearBuffer!")
            raise

    def ReadChannelErrInfo(self, chn_handle):
        try:
            ErrInfo = ZCAN_CHANNEL_ERR_INFO()
            ret = self.__dll.ZCAN_ReadChannelErrInfo(chn_handle, byref(ErrInfo))
            return ErrInfo if ret == ZCAN_STATUS_OK else None
        except:
            print("Exception on ZCAN_ReadChannelErrInfo!")
            raise

    def ReadChannelStatus(self, chn_handle):
        try:
            status = ZCAN_CHANNEL_STATUS()
            ret = self.__dll.ZCAN_ReadChannelStatus(chn_handle, byref(status))
            return status if ret == ZCAN_STATUS_OK else None
        except:
            print("Exception on ZCAN_ReadChannelStatus!")
            raise

    def GetReceiveNum(self, chn_handle, can_type = ZCAN_TYPE_CAN):
        try:
            return self.__dll.ZCAN_GetReceiveNum(chn_handle, can_type)
        except:
            print("Exception on ZCAN_GetReceiveNum!")
            raise

    def Transmit(self, chn_handle, std_msg, len):
        try:
            return self.__dll.ZCAN_Transmit(chn_handle, byref(std_msg), len)
        except:
            print("Exception on ZCAN_Transmit!")
            raise

    def Receive(self, chn_handle, rcv_num, wait_time = c_int(-1)):
        try:
            rcv_can_msgs = (ZCAN_Receive_Data * rcv_num)()
            ret = self.__dll.ZCAN_Receive(chn_handle, byref(rcv_can_msgs), rcv_num, wait_time)
            return rcv_can_msgs, ret
        except:
            print("Exception on ZCAN_Receive!")
            raise
    
    def TransmitFD(self, chn_handle, fd_msg, len):
        try:
            return self.__dll.ZCAN_TransmitFD(chn_handle, byref(fd_msg), len)
        except:
            print("Exception on ZCAN_TransmitFD!")
            raise
    
    def ReceiveFD(self, chn_handle, rcv_num, wait_time = c_int(-1)):
        try:
            rcv_canfd_msgs = (ZCAN_ReceiveFD_Data * rcv_num)()
            ret = self.__dll.ZCAN_ReceiveFD(chn_handle, byref(rcv_canfd_msgs), rcv_num, wait_time)
            return rcv_canfd_msgs, ret
        except:
            print("Exception on ZCAN_ReceiveFD!")
            raise

    def GetIProperty(self, device_handle):
        try:
            self.__dll.GetIProperty.restype = POINTER(IProperty)
            return self.__dll.GetIProperty(device_handle)
        except:
            print("Exception on ZCAN_GetIProperty!")
            raise

    def SetValue(self, iproperty, path, value):
        try:
            func = CFUNCTYPE(c_uint, c_char_p, c_char_p)(iproperty.contents.SetValue)
            return func(c_char_p(path.encode("utf-8")), c_char_p(value.encode("utf-8")))
        except:
            print("Exception on IProperty SetValue")
            raise
            
    def SetValue1(self, iproperty, path, value):                                              #############################
        try:
            func = CFUNCTYPE(c_uint, c_char_p, c_char_p)(iproperty.contents.SetValue)
            return func(c_char_p(path.encode("utf-8")), c_void_p(value))
        except:
            print("Exception on IProperty SetValue")
            raise
            

    def GetValue(self, iproperty, path):
        try:
            func = CFUNCTYPE(c_char_p, c_char_p)(iproperty.contents.GetValue)
            return func(c_char_p(path.encode("utf-8")))
        except:
            print("Exception on IProperty GetValue")
            raise

    def ReleaseIProperty(self, iproperty):
        try:
            return self.__dll.ReleaseIProperty(iproperty)
        except:
            print("Exception on ZCAN_ReleaseIProperty!")
            raise
###############################################################################
'''
USBCANFD-MINI Demo
'''
def canfd_start(zcanlib, device_handle, chn):
    ip = zcanlib.GetIProperty(device_handle)
    ret = zcanlib.SetValue(ip, str(chn) + "/canfd_standard", "0")
    if ret != ZCAN_STATUS_OK:
        print("Set CH%d CANFD standard failed!" %(chn))
        exit(0)
    ret = zcanlib.SetValue(ip, str(chn) + "/initenal_resistance", "1")
    if ret != ZCAN_STATUS_OK:
        print("Open CH%d resistance failed!" %(chn))
        exit(0)
    ret = zcanlib.SetValue(ip,str(chn)+"/canfd_abit_baud_rate","500000")  #设置波特率
    ret = zcanlib.SetValue(ip,str(chn)+"/canfd_dbit_baud_rate","2000000")
    if ret != ZCAN_STATUS_OK:
        print("Set CH%d baud failed!" %(chn))      
        exit(0)
        
    ret = zcanlib.SetValue(ip, "0/set_cn","A001")
    if ret == ZCAN_STATUS_OK:
        t = zcanlib.GetValue(ip, "0/get_cn/1")
        print(type(t)) 
        print(str(t))   
        

    chn_init_cfg = ZCAN_CHANNEL_INIT_CONFIG()
    chn_init_cfg.can_type = ZCAN_TYPE_CANFD
    chn_init_cfg.config.canfd.mode  = 0
    chn_handle = zcanlib.InitCAN(device_handle, chn, chn_init_cfg)
    if chn_handle ==0:
        print("initCAN failed!" %(chn))  
        exit(0)
###SET filter  
    ret = zcanlib.SetValue(ip,str(chn)+"/filter_clear","0")
    if ret != ZCAN_STATUS_OK:
        print("Set CH%d  filter_clear failed!" %(chn))
        exit(0)
    ret = zcanlib.SetValue(ip,str(chn)+"/filter_mode","0")    #标准帧滤波
    if ret != ZCAN_STATUS_OK:
        print("Set CH%d  filter_mode failed!" %(chn)) 
        exit(0)
    ret = zcanlib.SetValue(ip,str(chn)+"/filter_start","0")    
    if ret != ZCAN_STATUS_OK:
        print("Set CH%d  filter_start failed!" %(chn))  
        exit(0)        
    ret = zcanlib.SetValue(ip,str(chn)+"/filter_end","0x7FF")    
    if ret != ZCAN_STATUS_OK:
        print("Set CH%d  filter_end failed!" %(chn)) 
        exit(0)
    ret = zcanlib.SetValue(ip,str(chn)+"/filter_mode","1")    #扩展帧滤波
    if ret != ZCAN_STATUS_OK:
        print("Set CH%d  filter_mode failed!" %(chn))
        exit(0)
    ret = zcanlib.SetValue(ip,str(chn)+"/filter_start","0")    
    if ret != ZCAN_STATUS_OK:
        print("Set CH%d  filter_start failed!" %(chn))
        exit(0)        
    ret = zcanlib.SetValue(ip,str(chn)+"/filter_end","0x1FFFFFFF")    
    if ret != ZCAN_STATUS_OK:
        print("Set CH%d  filter_end failed!" %(chn))
        exit(0)
    ret = zcanlib.SetValue(ip,str(chn)+"/filter_ack","0")    
    if ret != ZCAN_STATUS_OK:
        print("Set CH%d  filter_ack failed!" %(chn))
        exit(0)

    ret=zcanlib.StartCAN(chn_handle)
    if ret != ZCAN_STATUS_OK:
        print("startCAN failed!" %(chn))
        exit(0)  

### Set Auto Transmit   
    ret = zcanlib.SetValue(ip,str(chn)+"/clear_auto_send","0")
    if ret != ZCAN_STATUS_OK:
        print("Clear CH%d USBCANFD AutoSend failed!" %(chn))
        exit(0)

    path = str(chn)+"/auto_send"
    func = CFUNCTYPE(c_uint, c_char_p, c_void_p)(ip.contents.SetValue)
    ret = func(c_char_p(path.encode("utf-8")), cast(byref(AutoCAN_A), c_void_p))
    ret = func(c_char_p(path.encode("utf-8")), cast(byref(AutoCAN_B), c_void_p))  
    path = str(chn)+"/auto_send_param"
    ret = func(c_char_p(path.encode("utf-8")), cast(byref(AutoCAN_B_delay), c_void_p))  #delay 100ms
    '''   
    ret = zcanlib.SetValue(ip,str(chn)+"/apply_auto_send","0")  
    if ret != ZCAN_STATUS_OK:
        print("Apply CH%d USBCANFD AutoSend failed!" %(chn))
        exit(0)
    '''
 
    zcanlib.ReleaseIProperty(ip) 
    return chn_handle

zcanlib = ZCAN() 
testcantype =0 #0:CAN; 1:canfd
handle = zcanlib.OpenDevice(ZCAN_USBCANFD_MINI, 0,0)
if handle == INVALID_DEVICE_HANDLE:
    print("Open CANFD Device failed!")
    exit(0)
print("device handle:%d." %(handle))

info = zcanlib.GetDeviceInf(handle)
print("Device Information:\n%s" %(info))

#set auto send obj
AutoCAN_A    =  ZCAN_AUTO_TRANSMIT_OBJ()
AutoCAN_B    =  ZCAN_AUTO_TRANSMIT_OBJ()
AutoCAN_A.enable                    = 1  #enable
AutoCAN_A.index                     = 0
AutoCAN_A.interval                  = 200  #ms
AutoCAN_A.obj.frame.can_id          = 0x100
AutoCAN_A.obj.transmit_type         = 0
AutoCAN_A.obj.frame.eff             = 0
AutoCAN_A.obj.frame.rtr             = 0
AutoCAN_A.obj.frame.can_dlc         = 8
for j in range(AutoCAN_A.obj.frame.can_dlc):
    AutoCAN_A.obj.frame.data[j] = j

AutoCAN_B.enable                    = 1  #enable
AutoCAN_B.index                     = 1
AutoCAN_B.interval                  = 200  #ms
AutoCAN_B.obj.frame.can_id          = 0x300
AutoCAN_B.obj.transmit_type         = 0
AutoCAN_B.obj.frame.eff             = 0
AutoCAN_B.obj.frame.rtr             = 0
AutoCAN_B.obj.frame.can_dlc         = 8
for j in range(AutoCAN_B.obj.frame.can_dlc):
    AutoCAN_B.obj.frame.data[j] = j

AutoCAN_B_delay=ZCANFD_AUTO_TRANSMIT_OBJ_PARAM()
AutoCAN_B_delay.index = AutoCAN_B.index
AutoCAN_B_delay.type  = 1
AutoCAN_B_delay.value = 100

#Start CAN

chn_handle = canfd_start(zcanlib, handle, 0)
print("channel handle:%d." %(chn_handle))

#Send CAN Messages
def can_transmit(data,count):
    msgs = (ZCAN_Transmit_Data * count)()
    for i in range(count):
        msgs[i].transmit_type = 0 #0-正常发送，2-自发自收
        msgs[i].frame.eff     = 0 #0-标准帧，1-扩展帧
        msgs[i].frame.rtr     = 0 #0-数据帧，1-远程帧
        msgs[i].frame.can_id  = 0x260
        msgs[i].frame.can_dlc = 8
        for j in range(msgs[i].frame.can_dlc):
            msgs[i].frame.data[j] =data[j]
    ret = zcanlib.Transmit(chn_handle, msgs, count)
    print("Tranmit Num: %d." % ret)
"""
#Send CANFD Messages
transmit_canfd_num = 10
canfd_msgs = (ZCAN_TransmitFD_Data * transmit_canfd_num)()
for i in range(transmit_canfd_num):
    canfd_msgs[i].transmit_type = 0 #0-正常发送，2-自发自收
    canfd_msgs[i].frame.eff     = 0 #0-标准帧，1-扩展帧
    canfd_msgs[i].frame.rtr     = 0 #0-数据帧，1-远程帧
    canfd_msgs[i].frame.brs     = 1 #BRS 加速标志位：0不加速，1加速
    canfd_msgs[i].frame.can_id  = i
    canfd_msgs[i].frame.len     = 8
    for j in range(canfd_msgs[i].frame.len):
        canfd_msgs[i].frame.data[j] = j
ret = zcanlib.TransmitFD(chn_handle, canfd_msgs, transmit_canfd_num)
print("Tranmit CANFD Num: %d." % ret)
thread=threading.Thread(target=input_thread)
thread.start()

#Receive Messages
while True:
    rcv_num = zcanlib.GetReceiveNum(chn_handle, ZCAN_TYPE_CAN)
    rcv_canfd_num = zcanlib.GetReceiveNum(chn_handle, ZCAN_TYPE_CANFD)
    if rcv_num:
        print("Receive CAN message number:%d" % rcv_num)
        rcv_msg, rcv_num = zcanlib.Receive(chn_handle, rcv_num)
        for i in range(rcv_num):
            print("[%d]:timestamps:%d,type:CAN, id:%s, dlc:%d, eff:%d, rtr:%d, data:%s" %(i, rcv_msg[i].timestamp, 
                    hex(rcv_msg[i].frame.can_id), rcv_msg[i].frame.can_dlc, 
                    rcv_msg[i].frame.eff, rcv_msg[i].frame.rtr,
                    ''.join(hex(rcv_msg[i].frame.data[j])+ ' 'for j in range(rcv_msg[i].frame.can_dlc))))
    elif rcv_canfd_num:
        print("Receive CANFD message number:%d" % rcv_canfd_num)
        rcv_canfd_msgs, rcv_canfd_num = zcanlib.ReceiveFD(chn_handle, rcv_canfd_num, 1000)
        for i in range(rcv_canfd_num):
            print("[%d]:timestamp:%d,type:canfd, id:%s, len:%d, eff:%d, rtr:%d, esi:%d, brs: %d, data:%s" %(
                    i, rcv_canfd_msgs[i].timestamp, hex(rcv_canfd_msgs[i].frame.can_id), rcv_canfd_msgs[i].frame.len,
                    rcv_canfd_msgs[i].frame.eff, rcv_canfd_msgs[i].frame.rtr, 
                    rcv_canfd_msgs[i].frame.esi, rcv_canfd_msgs[i].frame.brs,
                    ''.join(hex(rcv_canfd_msgs[i].frame.data[j]) + ' ' for j in range(rcv_canfd_msgs[i].frame.len))))
    else:
        if thread.is_alive() == False:
            break
"""