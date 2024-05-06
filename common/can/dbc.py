import cantools
from common.logger.logger import logger

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