#! /usr/bin/env python



"""
this module combine all columns of test case and make them a test case and also provide interface to case generator
"""

try:
    from common.logger.logger import logger
except (ImportError, ModuleNotFoundError) as e:
    import logging as logger
from common.tc.conf import ITEMS
from common.tc.base import *
import json
import os
import codecs

class TC:
    def __init__(self, data: dict):
        allure_description = []
        for item in ITEMS:
            if len(item) == 2:
                j_name, c_name = item
                delimiter = None
            elif len(item) == 3:
                j_name, c_name, delimiter = item
            else:
                raise ValueError(f"the length of mapping table must be 2 or 3: {item}")

            # verifying data and trying to convert data into list or tuple
            if j_name not in data:
                raise KeyError(f"there's no key named: {j_name} in test case data: {data}, please set mapping table correctly")
            value = data[j_name]
            if isinstance(value, str):
                try:
                    tmp_value = eval(value)
                except Exception:
                    tmp_value = None

                if tmp_value and isinstance(tmp_value, (list, tuple, dict)):
                    value = tmp_value

            # create allure description
            allure_description.append(c_name + ":")
            if isinstance(value, (list, tuple)):
                for v in value:
                    if v:
                        allure_description.append(f"    {v}")
            elif isinstance(value, dict):
                for key_, value_ in value:
                    allure_description.append(f"    {key_} = {value_}")
            else:
                if value:
                    allure_description.append(f"    {value}")

            # set data as one of instance's attribute
            if not delimiter:
                if isinstance(value, (list, tuple)):
                    setattr(self, c_name, eval(f"{c_name}({value}).value"))
                else:
                    setattr(self, c_name, eval(f"{c_name}('''{value}''').value"))
            else:
                if isinstance(value, (list, tuple)):
                    setattr(self, c_name, eval(f"{c_name}({value}, '{delimiter}').value"))
                else:
                    setattr(self, c_name, eval(f"{c_name}('''{value}''', '{delimiter}').value"))

        setattr(self, "AllureDescription", allure_description)

key_mapping = {
    "key": "TestId",
    "summary": "TestTitle",
    "desc": "TestDescription",
    "precondition": "TestPrecondition",
    "step": "TestStep",
    "expect": "TestExpectation",
    "type": "TestType",
    "tag": "TestTag",
    "priority": "TestPriority",
}

def read_json(file_path):
    with codecs.open(file_path, "r", encoding="utf-8") as file:
        json_data = json.load(file)
        for item in json_data:
            for new_key, old_key in key_mapping.items():
                item[new_key] = item.pop(old_key)
    logger.info(f"{json_data}")
    with codecs.open(file_path, "w", encoding="utf-8") as file:
        json.dump(json_data, file, indent=2, ensure_ascii=False)
    file.close()



if __name__ == "__main__":
    # case = {
    #     "key": "id-1",
    #     "summary": "这是一个测试",
    #     "desc": "",
    #     "precondition": ["BAT ON", "KL15 ON", "Vehicle_Config_ENGINE_CONTROL_UNIT=00001(发动机控制单元)"],
    #     "step": """1.Send 0x371:EngClntTempWarn=1\n2.WAIT=1000\n3.Button:shortpress back""",
    #     "expect": """常显“发动机水温过高”报警，无声音\nPic_发动机水温过高报警=90\nOCR_发动机水温过高报警_ocr=发动机水温过高""",
    #     "type": "Auto",
    #     "status": "normal",
    #     "tag": "V3.5, B02",
    #     "priority": "",
    #     "req": "",
    #     "comment": "",
    #     "jiraid": ""
    # }

    file_path = r"E:\cluster_new\input\input_case\test_tell2.json"
    json_data = read_json(file_path=file_path)
    # tc = TC(get_dict)
    # print(tc.__dict__)
