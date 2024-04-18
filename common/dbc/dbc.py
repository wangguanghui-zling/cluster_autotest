#! /usr/bin/env python



"""
this module parsed dbc data from file xxx.dbc and store all messages in json file
directly use json file if dbc file has no change
delete json file if dbc file updated and new json file will be generated automatically

how to use:
    from common import DBC
    import json

    with open(dbc().dbc, "r") as f:
        messages = json.load(f)
"""

try:
    from common.logger.logger import logger
except (ImportError, ModuleNotFoundError) as e:
    import logging as logger
from common.dbc.base import BO, BABO, BASG, VAL
import json
import os
import copy
import re


class _DBCParser:
    def __init__(self, file: str):
        self.__file = file
        if not os.path.exists(self.__file):
            logger.error(f"dbc file not found: <{self.__file}>")
            raise FileNotFoundError(f"dbc file not found: <{self.__file}>")
        self.messages = {}
        self.parse_dbc()

    def extract(self):
        """
        extract all dbc line and stored in different list
        @return:
            dict: a dict stores all lines for parsing
        """
        bo = []
        babo = []
        basg = []
        val = []
        _bo_tmp = []
        logger.debug(f"start extracting dbc lines and store useful lines to lists")
        for line in self.lines():
            try:
                line = line.decode("utf-8")
            except (UnicodeDecodeError,):
                line = line.decode("utf-8", errors='ignore')
                logger.warning(f"line contains characters that can not be decoded by 'utf-8': <{line}>")
            line = line.strip()
            if not line:
                continue

            if 'head' not in self.messages:
                self.messages.update({"head": {}})

            # store "BA_ type BO_ message_id value"
            if line.startswith("BA_ ") and 'BO_ ' in line:
                babo.append(line)
            # store "BA_ defaultValue/sendType SG_ message_id signal_name value"
            elif line.startswith("BA_ ") and 'SG_ ' in line:
                basg.append(line)
            # store BA_ "BusType" "CANFD";
            elif line.startswith("BA_ ") and 'BusType' in line:
                groups = re.match(r'BA_\s+"BusType"\s+"(CAN|CANFD)"\s*;', line, re.IGNORECASE)
                bus_type = groups.group(1) if groups else ""
                self.messages['head']['bus_type'] = bus_type
            # store BA_ "DBName" "P05_for_SC_CANFD_V5_0";
            elif line.startswith("BA_ ") and 'DBName' in line:
                groups = re.match(r'BA_\s+"DBName"\s+"(\w+)"\s*;', line, re.IGNORECASE)
                db_name = groups.group(1) if groups else ""
                self.messages['head']['db_name'] = db_name
            # store "VAL_ message_id signal_name keyValuePairs"
            elif line.startswith("VAL_ "):
                val.append(line)
            else:
                # store "BO_ message_id message_name: message_size node_name"
                if line.startswith("BO_ ") or line.startswith("SG_ "):
                    _bo_tmp.append(line)
                    if len(_bo_tmp) > 1 and line.startswith("BO_ "):
                        bo.append(_bo_tmp[:-1])
                        _bo_tmp = _bo_tmp[-1:]
                # store the last "BO_ message_id message_name: message_size node_name"
                elif _bo_tmp:
                    bo.append(_bo_tmp[:])
                    _bo_tmp.clear()
                # lines not used
                else:
                    logger.debug(f"dbc line ignored: <{line}>")

        return bo, babo, basg, val

    def parse_dbc(self):
        """
        parse all messages and signals from dbc
        """
        logger.debug(f"start parsing dbc lines extracted")
        bo, babo, basg, val = self.extract()

        # parsing "BO_ message_id message_name: message_size node_name"
        logger.debug(f'parsing "BO_ message_id message_name: message_size node_name"')
        for bo_line in bo:
            msg = BO(bo_line).value
            self.messages.update({msg['message_id']: msg})

        # parsing "BA_ type BO_ message_id value"
        logger.debug(f'parsing "BA_ type BO_ message_id value"')
        data = BABO(babo).value
        for msg_id, value in data.items():
            self.messages[msg_id].update(value)

        # parsing "BA_ defaultValue/sendType SG_ message_id signal_name value"
        logger.debug(f'parsing "BA_ defaultValue/sendType SG_ message_id signal_name value"')
        data = BASG(basg).value
        for msg_id, value in data.items():
            for type_, sig_name, val_ in value:
                if type_ == 'default_value':
                    # item_signal['default_value'] = int(default_value['default_value'] * float(item_signal['factor']) + float(item_signal['offset']))
                    val_ = int(val_ * float(self.messages[msg_id]['signals'][sig_name]['factor']) + float(
                        self.messages[msg_id]['signals'][sig_name]['offset']))
                self.messages[msg_id]['signals'][sig_name].update({type_: val_})

        # parsing "VAL_ message_id signal_name keyValuePairs"
        logger.debug(f'parsing "VAL_ message_id signal_name keyValuePairs"')
        data = VAL(val).value
        for msg_id, msg in self.messages.items():
            if msg_id == 'head':
                continue
            for sig_name, sig in msg['signals'].items():
                if msg_id in data and sig_name in data[msg_id]:
                    self.messages[msg_id]['signals'][sig_name]['values'] = data[msg_id][sig_name]
                else:
                    self.messages[msg_id]['signals'][sig_name]['values'] = {}

    def lines(self):
        """
        read dbc file line by line and return a generator
        @return:
            generator
        """
        with open(self.__file, 'rb') as pf:
            line = pf.readline()
            while line:
                yield line
                line = pf.readline()


class DBC:
    __instance = None
    Signals = {}

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __init__(self, file: str, searchList: (list, tuple) = None):
        """
        @param:
            file: absolute path or file name of .dbc file, <searchList> must be set if only file name passed in rather than absolute path
            searchList: a list of dirs used for searching .dbc file
        """
        self.__file = self.get_dbc_path(file, searchList)
        self.dbc = self.__file[:-4] + ".json"
        if not os.path.exists(self.dbc):
            self.messages = _DBCParser(self.__file).messages
            self.write_json_file()
        else:
            with open(self.dbc, 'r', encoding="utf-8") as f:
                self.messages = json.load(f)
            logger.info(
                f"json file parsed from dbc has been detected, directly use this. Please delete json first if you have updated dbc file")
        self.initial_value = self._initial()

    def _initial(self):
        """
        create or load a initial file which stores the initial value of signals
        @return:
            dict: a dict stores signal's initial value
        """
        path, file_name = os.path.split(self.__file)
        init_file = os.path.join(path, "initial.json")
        if os.path.exists(init_file):
            logger.info(f"initial file for signals exists, loading <{init_file}>")
            with open(init_file, 'r') as f:
                return json.load(f)
        else:
            init_json = {}
            for key_, item in self.messages.items():
                if "message_id" not in item or "signals" not in item:
                    logger.error(f"message can not be parsed as initial value: <{item}>")
                    continue
                for sk, sig in item["signals"].items():
                    value = '0'
                    if "values" in sig:
                        try:
                            value = list(sig["values"].keys())[0]
                        except (KeyError, IndexError):
                            value = '0'
                    init_json[f"{item['message_id']}-{sig['signal_name']}"] = value
            with open(init_file, 'w') as f:
                json.dump(init_json, f, indent=4)
            logger.info(f"initial file: <{init_file}> has been created successfully")

            return init_json

    def store_current_signal_value(
            self,
            msgId: (int, str) = None,
            sigName: str = None,
            sigData: str = None
    ):
        """
        store current signal value
        @param:
            msgId: str, message id
            sigName: str, signal name
            sigData: str, the data to be sent
        """
        if msgId and isinstance(msgId, str):
            if msgId.lower().startswith("0x"):
                msgId = int(msgId, 16)
            else:
                msgId = int(msgId)
        init_value_name = f"{str(msgId)}-{sigName}"
        if init_value_name in self.initial_value:
            if self.initial_value[init_value_name] != sigData:
                self.Signals[init_value_name] = sigData
                logger.debug(
                    f"signal sent: <{msgId}:{sigName}={sigData}> is different from default: <{msgId}:{sigName}={self.initial_value[init_value_name]}> and will be reset later")
            elif init_value_name in self.Signals:
                self.Signals.pop(init_value_name)
        else:
            logger.debug(f"signal: <{init_value_name}> did not define an initial value")

    def get_default_signal_values(self):
        """
        get all signals and corresponding default values
        @return:
            list: a serial of dict which stores message id, signal name and default signal value
        """
        values = []
        keys = list(self.Signals.keys())
        for index in range(len(keys)):
            default_value = self.initial_value[keys[index]]
            msgId, sigName = keys[index].split("-")
            values.append({"msgId": msgId, "sigName": sigName, "sigData": default_value})
            self.Signals.pop(keys[index])
        logger.debug(
            f"signals not in default value have been collected: <{values}>, buffer should be empty: <{self.Signals}>")

        return values

    def get_message(
            self,
            msgId: (int, str) = None,
            msgName: str = None,
            sigName: str = None
    ):
        """
        retrieve specific message frame and signal data, you can find a message by message_id or message_name
        @param:
            message_id: message id, used for searching message frame
            message_name: message name, used for searching message frame
            signal_name: signal name, used for searching a specific signal from message
        @return:
            dict: a dict for message
        """
        if msgId is None and msgName is None:
            logger.error(f"message id or message name must be specified")
            return None
        if msgId and isinstance(msgId, str):
            if msgId.lower().startswith("0x"):
                msgId = int(msgId, 16)
            else:
                msgId = int(msgId)
        logger.debug(f"message id is: {msgId}, message name: {msgName}, signal name: {sigName}")

        msgId = str(msgId)
        if msgId != "None" and msgId in self.messages:
            msg_bak = copy.deepcopy(self.messages[msgId])
        elif msgName:
            for msg_id, msg in self.messages.items():
                if msgName == msg["message_name"]:
                    msg_bak = copy.deepcopy(msg)
                    msgId = msg_id
                    break
            else:
                logger.error(f"can not find message according to message info: <message id={msgId}, message name={msgName}>")
                raise AttributeError(f"can not find message according to message: <message id={msgId}, message name={msgName}>")
        else:
            logger.error(f"can not find message according to message info: <message id={msgId}, message name={msgName}>")
            raise AttributeError(f"can not find message according to message info: <message id={msgId}, message name={msgName}>")

        if sigName:
            if sigName in self.messages[msgId]['signals']:
                msg_bak.update(self.messages[msgId]['signals'][sigName])
            else:
                logger.warning(f"can not find signal data according to signal info: <signal name={sigName}>, "
                               f"trying to search signal using lower case '{sigName.lower()}' and signal name without message id")
                signal_keys = self.messages[msgId]['signals'].keys()
                signal_keys_mapping = {str(x).lower(): x for x in signal_keys}
                if sigName.lower() in signal_keys_mapping:
                    msg_bak.update(self.messages[msgId]['signals'][signal_keys_mapping[sigName.lower()]])
                else:
                    newSigName = sigName.split("_0x")[0] if '_0x' in sigName else sigName.split("_0X")[0]
                    if newSigName in self.messages[msgId]['signals']:
                        msg_bak.update(self.messages[msgId]['signals'][newSigName])
                    elif newSigName.lower() in signal_keys_mapping:
                        msg_bak.update(self.messages[msgId]['signals'][signal_keys_mapping[newSigName.lower()]])
        del msg_bak['signals']
        logger.debug(f"msg found: {msg_bak}")
        return msg_bak

    def write_json_file(self):
        """
        create json file and store messages to json
        """
        with open(self.dbc, 'w', encoding="utf-8") as p_json:
            json.dump(self.messages, p_json, indent=4, ensure_ascii=False)
        logger.info("The dbc file has been parsed completely.")

    @staticmethod
    def get_dbc_path(file: str, searchList: (list, tuple) = None):
        """
        search dbc according to file provided, if file provided
        get dbc config from settings.ini if file not provided
        search dbc in project if file not provided and no config in settings.ini
        @param:
            file: absolute path or file name of .dbc file, <searchList> must be set if only file name passed in rather than absolute path
            searchList: a list of dirs used for searching .dbc file
        @return:
            str, absolute path of dbc file
        """
        searchPaths = [os.path.split(os.path.abspath(__file__))[0]]
        if searchList and isinstance(searchList, (list, tuple)):
            searchPaths.extend(list(searchList))

        # trying to find a dbc file from config folder and project folder with provided dbc name
        if file and os.path.exists(file) and file.lower().endswith(".dbc"):
            return file
        elif file and file.lower().endswith(".dbc"):
            for path in searchPaths:
                if not path:
                    logger.error(f"path for [config] or [root] has not been set in settings.ini")
                    continue
                for root_, dirs, files in os.walk(path):
                    if file in files:
                        return os.path.join(root_, file)
        else:
            # trying to search a dbc file from project root
            for path in searchPaths:
                if not path:
                    logger.error(f"path for [config] or [root] has not been set in settings.ini")
                    continue
                for root_, dirs, files in os.walk(path):
                    for f in files:
                        if f.lower().endswith(".dbc"):
                            return os.path.join(root_, f)

        raise FileNotFoundError(f"no dbc file has been detected with conditions: <file={file}> and <searchList={searchList}>")


if __name__ == "__main__":
    DBC(file=r"E:\cluster_new\common\can\canoe_project\A8E_Proj_IHU_PFET_CMX+V1.25_20230421.dbc")
