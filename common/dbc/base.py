#! /usr/bin/env python



try:
    from common.logger.logger import logger
except (ImportError, ModuleNotFoundError) as e:
    import logging as logger
from common.dbc.dt import VFrameFormat, GenMsgILSupport
import re


class BO:
    """
    parse message and signals:
        BO_ 763 VMDR1: 8 GW
        SG_ MbrMonrEnaSts : 15|1@0+ (1,0) [0|0] ""  HUT
    """

    BO_Pattern = re.compile(r'BO_\s+(\d+)\s+(\w+)\s*:\s*(\d+)\s+(\w+).*', re.IGNORECASE)
    SG_Pattern = re.compile(r'SG_\s+(\w+)\s*:\s*(\d+)\s*\|\s*(\d+)\s*@\s*([01]+)\s*([\+-]+)\s+\((.+),(.+)\)\s+\[(.+)\|(.+)\]\s+\"(.*)\"\s+(.*)', re.IGNORECASE)
    BO_Item = ("message_id", "message_name", "message_size", "node_name")
    SG_Item = ("signal_name", "raw_start_bit", "signal_size", "byte_order", "value_type", "factor", "offset", "min_value", "max_value", "unit", "receiver")

    def __init__(self, data: (str, list, tuple)):
        self.value = {}
        if not data:
            logger.error(f"DBC, no massage data received")

        if isinstance(data, str):
            data = data.split("\n")
        for item in data:
            item = item.replace("\n", "").replace("\r", "")
            item = item.strip()
            # parse BO_ xxx
            if item.startswith("BO_ "):
                msg = self.BO_Pattern.match(item).groups()
                if not msg or len(msg) != len(self.BO_Item):
                    logger.error(f"DBC, message can not be parsed: {item}")
                    raise ValueError(f"DBC, message can not be parsed: {item}")
                self.value = dict(zip(self.BO_Item, msg))
            # parse SG_ xxx
            elif 'message_id' in self.value and item.startswith("SG_ "):
                if 'signals' not in self.value:
                    self.value['signals'] = {}
                sig = self.SG_Pattern.match(item).groups()
                if not sig or len(sig) != len(self.SG_Item):
                    logger.error(f"DBC, signal can not be parsed: {item}")
                    raise ValueError(f"DBC, signal can not be parsed: {item}")
                signal = dict(zip(self.SG_Item, sig))
                signal = self.bit_sequence(signal)
                self.value['signals'].update({signal['signal_name']: signal})
            # error
            else:
                logger.error(f"DBC, message data incorrect: {item}")
                raise EOFError(f"DBC, message data incorrect: {item}")

    @staticmethod
    def bit_sequence(dic: dict):
        """
        calculate bit order
        @param:
            dic: a dict for signal
        @return:
            dict: return a dict calculated
        """
        # 1.将一个位的位序号从lsb0转换到msb0的位序号（或msb0到lsb0):
        #   b = b - (b % 8) + 7 - (b % 8)
        start_bit = int(dic['raw_start_bit']) - 2 * (int(dic['raw_start_bit']) % 8) + 7
        if dic['byte_order'] == '0':  # 大端或motorola字节序: lsb0
            # 2. 在msb0下，由一个信号的msb位序号转化得到lsb位序号:
            #   b = b+length-1
            start_bit = start_bit + int(dic['signal_size']) - 1
        else:
            # 小端或intel字节序: msb0
            # 2. 在msb0下，将一个信号的lsb位序号转化为msb位序号:
            #   b = b + 1 - length
            start_bit = start_bit - int(dic['signal_size']) + 1
        # 3. 将一个位的位序号从lsb0转换到msb0的位序号（或msb0到lsb0):
        #    b = b - (b % 8) + 7 - (b % 8)
        dic['start_bit'] = start_bit - 2 * (start_bit % 8) + 7

        logger.debug(f"DBC, start parsing signal: {dic['signal_name']}")

        return dic


class BABO:
    """
    parse: BA_ xxx BO_ xxx
    """

    BA_BO_Pattern = re.compile(r'BA_\s+"(\w+)"\s+BO_\s+(\d+)\s+(\d+)\s*;', re.IGNORECASE)
    BA_BO_Item = ("attribute_name", "message_id", "attribute_value")

    Attrs = {
        'GenMsgSendType': ('send_type', None),
        'GenMsgILSupport': ('IL_support', GenMsgILSupport),
        'GenMsgCycleTime': ('cycle_time', None),
        'VFrameFormat': ('frame_format', VFrameFormat),
        'NmMessage': ('network_manage_message', None),
        'DiagState': ('diagnose_state', None),
    }

    def __init__(self, data: (str, list, tuple)):
        self.value = {}
        if not data:
            logger.error(f"DBC, no <BA_ xxx BO_ xxx> data received")
            raise ValueError(f"no <BA_ xxx BO_ xxx> data received")

        if isinstance(data, str):
            data = data.split("\n")
        for item in data:
            item = item.replace("\n", "").replace("\r", "")
            item = item.strip()
            if item.startswith("BA_") and "BO_" in item:
                attr = self.BA_BO_Pattern.match(item).groups()
                if not attr or len(attr) != len(self.BA_BO_Item):
                    logger.warning(f"DBC, can not parse BA_ xxx BO_ xxx: <{item}>")
                    continue
                attr_name, message_id, attr_value = attr
                if message_id not in self.value:
                    self.value[message_id] = {}
                if attr_name in self.Attrs:
                    self.value[message_id][self.Attrs[attr_name][0]] = self.Attrs[attr_name][1][attr_value] if self.Attrs[attr_name][1] else attr_value
                else:
                    logger.warning(f"DBC, line will be ignored: <{item}>")
        for key_, value_ in self.value.items():
            if 'send_type' not in value_ and 'cycle_time' in value_ and int(value_['cycle_time']) > 0:
                self.value[key_]['send_type'] = '0'


class BASG:
    """
    parse:
        BA_ "GenSigStartValue" SG_ MessageId SignalName DefaultValue;
        BA_ "GenSigSendType" SG_ MessageId SignalName DefaultValue;
    """

    BA_SG_Pattern = re.compile(r'BA_\s+"(\w+)"\s+SG_\s+(\d+)\s+(\w+)\s+(\d+|"\w+")\s*;', re.IGNORECASE)
    BA_SG_Item = ("type", "message_id", "sig_name", "value")

    Attrs = {
        'GenSigStartValue': 'default_value',
        'GenSigSendType': 'send_type',
        'GenSigCycleTime': 'cycle_time',
        'SystemSignalLongSymbol': 'long_name',
    }

    def __init__(self, data: (str, list, tuple)):
        self.value = {}
        if not data:
            logger.error(f"DBC, no <BA_ xxx SG_ xxx> data received")
            raise ValueError(f"no <BA_ xxx SG_ xxx> data received")

        if isinstance(data, str):
            data = data.split("\n")
        for item in data:
            item = item.replace("\n", "").replace("\r", "")
            item = item.strip()
            if item.startswith("BA_") and "SG_" in item:
                attr = self.BA_SG_Pattern.match(item)
                if attr:
                    attr = attr.groups()
                    if not attr or len(attr) != len(self.BA_SG_Item):
                        logger.warning(f"DBC, can not parse BA_ xxx SG_ xxx: <{item}>")
                        continue
                    type_, message_id, sig_name, value = attr
                    if message_id not in self.value:
                        self.value[message_id] = []
                    # item_signal['default_value'] = int(default_value['default_value'] * float(item_signal['factor']) + float(item_signal['offset']))
                    if type_ in self.Attrs:
                        self.value[message_id].append((self.Attrs[type_], sig_name, eval(value)))
                    else:
                        logger.warning(f"DBC, line will be ignored: <{item}>")
                else:
                    logger.warning(f"DBC, line will be ignored: <{item}>")


class VAL:
    """
    parse:
        VAL_ MessageId SignalName N “DefineN” …… 0 “Define0”;
    """

    VAL_Pattern = re.compile(r'VAL_\s+(\d+)\s+(\w+)\s+(.*)\s*;', re.IGNORECASE)
    VAL_Item = ("message_id", "signal_name", "values")

    def __init__(self, data: (str, list, tuple)):
        self.value = {}
        if not data:
            logger.error(f"DBC, no <VAL_ MessageId SignalName N “DefineN” …… 0 “Define0”;> data received")
            raise ValueError(f"DBC, no <VAL_ MessageId SignalName N “DefineN” …… 0 “Define0”;> data received")

        if isinstance(data, str):
            data = data.split("\n")
        for item in data:
            item = item.replace("\n", "").replace("\r", "")
            item = item.strip()
            if item.startswith("VAL_"):
                attr = self.VAL_Pattern.match(item).groups()
                if not attr or len(attr) != len(self.VAL_Item):
                    logger.warning(f"DBC, can not parse VAL_ xxx: <{item}>")
                    continue
                message_id, sig_name, values = attr
                values = [x.strip() for x in values.split('"') if x.strip()]
                if len(values) % 2 != 0:
                    logger.error(f"DBC, can not parse values: <{item}>")
                    raise ValueError(f"DBC, can not parse values: <{item}>")
                if message_id not in self.value:
                    self.value[message_id] = {}
                if sig_name not in self.value[message_id]:
                    self.value[message_id][sig_name] = dict(zip(values[::2], values[1::2]))
                else:
                    logger.error(f"DBC, signal already exists: <{item}>")
                    raise ValueError(f"DBC, signal already exists: <{item}>")


if __name__ == "__main__":
    VAL_Value_Pattern = re.compile(r'\s*(\d+)\s+"\s*([\w\s]+)\s*"', re.IGNORECASE)
    print(VAL_Value_Pattern.findall('0 " Lamp off " 1 " Lamp on " 2 " Reserved " 3 " Lamp  blink & sound remind "'))
