#! /usr/bin/env python



"""
search for file named "test_xxx.json" and parse file and create a .py scripts
"""

import json
import os
import time
import shutil
try:
    from common.logger.logger import logger
except (ImportError, ModuleNotFoundError) as e:
    import logging as logger
from common.tc.template import Template
from common.tc.conf import Pattern
from common.tc.case import TC


class Gen:
    def __init__(self, path: str = None, file: (str, list, tuple) = None):
        if not path or not os.path.exists(path):
            logger.error(f"the path({path}) is not available")
            raise FileNotFoundError(f"the path({path}) is not available")
        self.__path = path
        self.fl = []
        if file:
            if isinstance(file, str):
                file = [file]
            for f in file:
                if os.path.isfile(f):
                    folder, f_name = os.path.split(f)
                    if str(f_name).lower().startswith("test_") and str(f_name).lower().endswith(".json"):
                        self.fl.append(f)
                else:
                    result = self._find_json(f)
                    if result:
                        self.fl.append(result)
        else:
            self.fl = self._find_json()
        if not self.fl:
            raise IndexError(f"no source data('test_xxx_xxx.json') found, no test case will be created.")

    def _find_json(self, fn: str = None):
        """
        find .json file if file name specified
        find all .json file which starts with 'test_'
        @param:
            fn: name of .json file
        @return:
            one or a list of .json files
        """
        file_list = []
        root_dir = self.__path
        for root, dirs, files in os.walk(root_dir):
            if root == root_dir or (root != root_dir and os.path.split(root)[1].lower().startswith("test_")):
                for f in files:
                    if f.lower().startswith("test_") and f.lower().endswith(".json"):
                        if fn and fn in f:
                            return os.path.join(root, f)
                        else:
                            file_list.append(os.path.join(root, f))

        return file_list

    def clear_scripts(self):
        """
        delete all test scripts(in format 'test_xxx_xxx.py'), to make sure only newest test scripts will be executed
        """
        logger.info(f"start searching for test scripts with old version and deleting it...")
        root_dir = self.__path
        for root, dirs, files in os.walk(root_dir):
            if root == root_dir or (root != root_dir and os.path.split(root)[1].lower().startswith("test_")):
                for f in files:
                    if f.lower().startswith("test_") and f.lower().endswith(".py"):
                        path = os.path.join(root, f)
                        os.remove(path)
                        for _ in range(100):
                            if not os.path.exists(path):
                                break
                            time.sleep(0.01)

    def run(self, count: int = 100):
        """
        1.clear all test scripts(in format test_xxx_xxx.py) in folders starts with 'test_' if clear is set
        2.read all source data files(in format text_xxx_xxx.json) and load as a list
        3.create and open a .py file which is in same path with the corresponding .json file
        4.write file header and import codes to .py file
        5.read all test data circularly and parsed them into codes and write them to .py file
        @param:
            count: every .py test script contains 'count' test cases, default to 100
        """
        # if clear:
        #     self.clear_scripts()
        for source in self.fl:
            # load json file as an object
            tc_folder = source.replace(".json", "")
            with open(source, 'r', encoding="utf-8") as f:
                tc_data = json.load(f)
            json_len = len(tc_data)
            if json_len < 1:
                logger.error(f"source data file: '{source}' has no data for test case, skipped")
                continue

            # clear folder before regenerate
            if os.path.exists(tc_folder):
                shutil.rmtree(tc_folder)
                for _ in range(100):
                    if not os.path.exists(tc_folder):
                        break
                    time.sleep(0.01)
            if not os.path.exists(tc_folder):
                os.makedirs(tc_folder)

            # start generate test scripts and divide
            script_num = json_len // count + 1 if json_len % count else json_len // count
            for num in range(script_num):
                tc_file = os.path.join(tc_folder, f"{os.path.split(tc_folder)[1]}_{num * count}_{num * count + count - 1}.py")
                with Template(tc_file) as f:
                    # f.module_header()
                    # f.module_doc()
                    f.module_import()
                    # f.module_globals()
                    f.class_name(os.path.split(source)[1])
                    # f.class_doc()
                    # f.class_setup(["API.reset_measurement()", "API.reset_battery()"])
                    f.class_setup(["API.reset_measurement()"])
                    f.class_teardown(["# API.close()"])
                    # f.method_setup(["API.reset_battery()"])
                    f.method_setup()
                    # f.method_teardown(["API.reset_battery()", "API.reset_signals()"])
                    # f.method_teardown(["API.reset_battery()"])
                    if num == script_num - 1:
                        s_data = tc_data[num * count:]
                    else:
                        s_data = tc_data[num * count: num * count + count]
                    for data in s_data:
                        if not isinstance(data, dict):
                            logger.error(f"data: '{data}' from: '{source}' could not be parsed, data must be a dict, skipped")
                            continue
                        tc = TC(data)
                        f.TestCase.allure_id(tc.TestId)
                        f.TestCase.allure_title(f"{tc.TestId}({tc.TestTitle})")
                        f.TestCase.allure_description(tc.AllureDescription)
                        f.TestCase.allure_tag(tc.TestTag)
                        # f.TestCase.pytest_mark()
                        f.TestCase.test_name(tc.TestId)
                        # f.TestCase.test_doc()
                        f.TestCase.test_precondition(Pattern.parse_to_code(tc.TestPrecondition))
                        f.TestCase.test_step(Pattern.parse_to_code(tc.TestStep))
                        f.TestCase.test_assert(Pattern.parse_to_code(tc.TestExpectation))
                logger.info(f"successfully created test scripts: {tc_file} with test data file: {source}")


if __name__ == "__main__":
    test = Gen(r"E:\cluster_new\input\input_case")
    test.run()
