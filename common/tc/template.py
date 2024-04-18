#! /usr/bin/env python



"""
create a python file and write test case data to the file
"""

import os
try:
    from common.logger.logger import logger
except (ImportError, ModuleNotFoundError) as e:
    import logging as logger
from common.tc.conf import ITEMS


SPACE_4 = " " * 4
SPACE_8 = " " * 8
SPACE_12 = " " * 12
SPACE_16 = " " * 16


def add_linebreak(data: (str, list, tuple), ch: str = "\n"):
    """
    add linebreak for each line
    @param:
        data: data which supposed to be appended a linebreak
        ch: linebreak, default to "\n"
    @return:
        str, list: data with linebreak
    """
    if isinstance(data, str):
        return data + ch if not data.endswith("\n") else data
    else:
        return [x + ch if not x.endswith("\n") else x for x in data]


class Template:
    def __init__(self, filename: str, mode: str = "w"):
        self.fn = filename
        self.mode = mode
        logger.info(f"start generating test scripts for pytest, file name is : {filename}")

    def __enter__(self):
        if self.fn.endswith(".py"):
            self.f = open(self.fn, mode=self.mode, encoding="utf-8")
            self.TestCase.clear_buffer()
            return self
        else:
            raise NameError(f"file could not be recognized by pytest: {self.fn}")

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.f.writelines(self.TestCase.buffer)
        self.f.close()

    def module_header(self, header: (list, tuple) = None):
        pass

    def module_doc(self, doc: (list, tuple) = None):
        pass

    def module_import(self, pck: (list, tuple) = None):
        if not pck:
            pck = [
                "from common import logger",
                # "from common import Config",
                "import allure",
                "import sys",
                "import pytest",
                # "sys.path.append(Config.test)",
                "from api import API"
            ]
        pck.append("\n\n")
        self.f.writelines(add_linebreak(pck))

    def module_globals(self, glb: (list, tuple) = None):
        pass

    def class_name(self, name: str = "TestProject"):
        if "_" in name:
            name = name.split("_")
            if name[0].lower() != "test":
                name = ["test"] + name
            if name[-1].lower().endswith(".json"):
                name[-1] = name[-1].replace(".json", "")
            elif name[-1].lower().endswith(".py"):
                name[-1] = name[-1].replace(".py", "")
            name = "class " + "".join([x.capitalize() for x in name]) + ":"
        else:
            if name.lower().startswith("test"):
                name = f"class Test{name[4:].capitalize()}:"
            else:
                name = f"class Test{name.capitalize()}:"
        self.f.write(add_linebreak(name))

    def class_doc(self):
        pass

    def class_setup(self, steps: (list, tuple) = None):
        pre_append = [
            f'''{SPACE_4}def setup_class(self):''',
            f'''{SPACE_8}logger.info(f"{{'=' * 30}} class setup {{'=' * 30}}")''',
                ]
        steps = pre_append + [SPACE_8 + x for x in steps] + ["\n"] if steps else pre_append + ["\n"]
        self.f.writelines(add_linebreak(steps))

    def class_teardown(self, steps: (list, tuple) = None):
        pre_append = [
            f'''{SPACE_4}def teardown_class(self):''',
            f'''{SPACE_8}logger.info(f"{{'=' * 30}} class teardown {{'=' * 30}}")''',
        ]
        steps = pre_append + [SPACE_8 + x for x in steps] + ["\n"]
        self.f.writelines(add_linebreak(steps))

    def method_setup(self, steps: (list, tuple) = None):
        pre_append = [
            f'''{SPACE_4}def setup_method(self, method):''',
            f'''{SPACE_8}logger.info(f"{{'*' * 10}} method setup: {{method.__name__}} {{'*' * 10}}")''',
        ]
        steps = pre_append + [SPACE_8 + x for x in steps] + ["\n"] if steps else pre_append + ["\n"]
        self.f.writelines(add_linebreak(steps))

    def method_teardown(self, steps: (list, tuple) = None):
        pre_append = [
            f'''{SPACE_4}def teardown_method(self, method):''',
            f'''{SPACE_8}logger.info(f"{{'*' * 10}} method teardown: {{method.__name__}} {{'*' * 10}}")''',
        ]
        steps = pre_append + [SPACE_8 + x for x in steps] + ["\n"] if steps else pre_append + ["\n"]
        self.f.writelines(add_linebreak(steps))

    class _TestCase:
        def __init__(self):
            self.buffer = []

        def clear_buffer(self):
            logger.debug(f"clear buffer of test cases")
            self.buffer = []

        def allure_id(self, id_: str):
            self.buffer.append(add_linebreak(f'''{SPACE_4}@allure.id("{id_}")'''))

        def allure_title(self, title: str):
            self.buffer.append(add_linebreak(f'''{SPACE_4}@allure.title("{title}")'''))

        def allure_description(self, desc: (list, tuple) = None):
            description = [
                f"{SPACE_4}@allure.description(",
                f'{SPACE_8}\"\"\"'
            ] + [SPACE_8 + x if "\n" not in x else SPACE_8 + x.replace("\n", "\n" + SPACE_12) for x in desc] + [
                f'{SPACE_8}\"\"\"',
                f"{SPACE_4})"
            ]
            self.buffer.extend(add_linebreak(description))

        def allure_tag(self, tag: (list, tuple) = None):
            if tag:
                self.buffer.append(add_linebreak(f'''{SPACE_4}@allure.tag(*{sorted(tag)})'''))

        def pytest_mark(self):
            pass

        def test_name(self, name: str):
            if not name.lower().startswith("test_"):
                name = "test_" + name
            self.buffer.append(add_linebreak(f'''{SPACE_4}def {name}(self):'''))

        def test_doc(self):
            pass

        def test_precondition(self, steps: (list, tuple)):
            steps = [f'{SPACE_8}logger.info(">>>test preconditions:")'] + [SPACE_8 + x for x in steps]
            self.buffer.extend(add_linebreak(steps))

        def test_step(self, steps: (list, tuple)):
            steps = [f'\n{SPACE_8}logger.info(">>>test steps:")'] + [SPACE_8 + x for x in steps]
            self.buffer.extend(add_linebreak(steps))

        def test_assert(self, steps: (list, tuple)):
            steps = [f'\n{SPACE_8}logger.info(">>>test assert:")'] + [SPACE_8 + x for x in steps] + [""]
            self.buffer.extend(add_linebreak(steps))

    TestCase = _TestCase()


if __name__ == "__main__":
    pass
