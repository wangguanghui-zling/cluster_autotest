#! /usr/bin/env python



import re
try:
    from common.logger.logger import logger
except (ImportError, ModuleNotFoundError) as e:
    import logging as logger


# this global tuple stores some settings for test case recognition, the first one is a key of source data which should be a dict
# loading from json or excel, the second one is the class name in base.py, and the third one is delimiter of data and it's optional
ITEMS = (
    ("key",             "TestId"),
    ("summary",         "TestTitle"),
    ("desc",            "TestDescription"),
    ("precondition",    "TestPrecondition"),
    ("step",            "TestStep"),
    ("expect",          "TestExpectation"),
    ("type",            "TestType"),
    # ("", "TestPlatform"),
    # ("", "TestProject"),
    ("status",          "TestCaseStatus"),
    ("tag",             "TestTag"),
    ("priority",        "TestPriority"),
    # ("", "TestSeverity"),
    # ("", "TestSuite"),
    # ("", "TestEpic"),
    # ("", "TestStory"),
    # ("", "TestFeature"),
    ("req",             "TestRequirement"),
    ("comment",         "TestComment"),
    # ("", "TestResult"),
    ("jiraid",          "TestJiraId"),
    # ("", "TestIssue"),
    # ("", "TestOperator"),
    # ("", "TestDateTime"),
)


class _Pattern:

    # operation
    PatternBattery = re.compile(r"(?:bat|battery|power|pow)\s*?(?: |=|)\s*?(on|off|on_nocheck)\s*(\(.*?\)|)", re.IGNORECASE)
    PatternKL15 = re.compile(r"(?:kl15|engine|ign|ignition)\s*?(?: |=|)\s*?(on|off)\s*(\(.*?\)|)", re.IGNORECASE)
    PatternWait = re.compile(r"wait\s*?=\s*?(\d+)\s*(\(.*?\)|)", re.IGNORECASE)
    PatternVehicleConfig = re.compile(r"vehicle_config_(\w+)\s*?=\s*?(\d+)\s*(\(.*?\)|)", re.IGNORECASE)
    PatternSendMsg = re.compile(r"send\s*(0x[a-fA-F0-9]+)\s*(?::|\d*)\s*(\w+)\s*?=\s*?(\d+)\s*(\(.*?\)|)", re.IGNORECASE)
    PatternSetVoltage = re.compile(r"(?:set|)\s*(?:volt|voltage|v|u|vol)\s*?=\s*?(\d+\.?\d*)[vV]?\s*(\(.*?\)|)", re.IGNORECASE)
    PatternButton = re.compile(r"button\s*(?::|\s*)\s*(shortpress|longpress)\s*(\w+)\s*(\(.*?\)|)", re.IGNORECASE)
    # PatternRelay = re.compile(r"", re.IGNORECASE)
    # PatternDiagnostic = re.compile(r"", re.IGNORECASE)
    # PatternNetworkStatus = re.compile(r"", re.IGNORECASE)
    # PatternLocalConfig = re.compile(r"", re.IGNORECASE)
    # PatternSignalLost = re.compile(r"", re.IGNORECASE)
    # result
    PatternImageCompare = re.compile(r"pic_(color_)?([\w\s，,\(\)\+\.]+)\s*=\s*([\w\s/，,\+\.]+)\s*(\(.*?\)|)", re.IGNORECASE)
    PatternOCR = re.compile(r"ocr_([\w\s，,\(\)\+\.]+)\s*=\s*([\w\s/，,\+\.]+)\s*(\(.*?\)|)", re.IGNORECASE)
    PatternSignal = re.compile(r"signal(?:_|\d*?|:|=|-|)\s*(0x[a-fA-F0-9]+)\s*(?::|=|\d*?|-)\s*(\w+)\s*=\s*([\w\d]+)\s*(\(.*?\)|)", re.IGNORECASE)
    # PatternDiagnosticResult = re.compile(r"", re.IGNORECASE)

    # todo, add more pattern here

    class _Code:
        """
        every pattern above mapping a method in current class, for example, you must add a method named "battery" if you
        have added a pattern named "PatternBattery" and method name must be in lower case
        """
        def battery(self, a, z):
            if str(a).lower() in ("on", "off"):
                return f"API.battery('{str(a)}')  # {z}"
            else:
                return f"API.battery('on', False)  # {z}"

        def kl15(self, a, z):
            return f'API.kl15("{str(a).lower()}")  # {z}'

        def wait(self, a, z):
            return f'API.wait({int(a)})  # {z}'

        def vehicleconfig(self, *args):
            arg = [x[:2] for x in args if len(x) >= 2]
            comments = [x[2] for x in args if len(x) >= 3]
            return [
                f'# {" | ".join(comments)}',
                f'API.set_vehicle_config(*{arg})'
            ]

        def sendmsg(self, a, b, c, z):
            return f'API.send("{a}", "{b}", "{c}")  # {z}'

        def setvoltage(self, a, z):
            return f'API.ps.set_voltage({float(a)})  # {z}'

        def button(self, a, b, z):
            return f'API.button("{a}", "{b}")  # {z}'

        def imagecompare(self, a, b, c, z):
            if str(a).lower() == "color_":
                return [
                    f'result, location, label = API.image_compare("{b}", threshold={float(c)}, gray=False)  # {z}',
                    f'assert result * 100 >= {float(c)}'
                ]
            else:
                return [
                    f'result, location, label = API.image_compare("{b}", threshold={float(c)}, gray=True)  # {z}',
                    f'assert result * 100 >= {float(c)}'
                ]

        def ocr(self, a, b, z):
            return [
                f'result, location = API.ocr_compare("{a}", ocrExpect="{b}")  # {z}',
                f'assert result == "{b}"'
            ]

        def signal(self, a, b, c, z):
            if isinstance(c, str) and re.match(r"0x[a-fA-F0-9]+", c.strip(), re.IGNORECASE):
                c = int(c, 16)
            return [
                f'result = API.get("{a}", "{b}")  # {z}',
                f'assert str(result) == str({c})'
            ]

    Code = _Code()

    def parser(self, value: str):
        """
        match one step in Precondition/Step/Expectation and parse step as slots which could be used for generating .py scripts
        @param:
            value: one step
        @return:
            tuple, a tuple of values corresponding to different action
        @example:
            "BAT ON" -> ('Battery', 'ON', '')
            "KL15 ON" -> ('KL15', 'ON', '')
            "Vehicle_Config_ENGINE_CONTROL_UNIT=00001(发动机控制单元)" -> ('VehicleConfig', 'ENGINE_CONTROL_UNIT', '00001', '(发动机控制单元)')
            "WAIT=5000" -> ('Wait', '5000', '')
            "Send 0x371:EngClntTempWarn=0" -> ('SendMsg', '0x371', 'EngClntTempWarn', '0', '')
            "Pic_发动机水温过高报警=90" -> ('ImageCompare', '发动机水温过高报警', '90', '')
            "OCR_发动机水温过高报警_ocr=发动机水温过高" -> ('OCR', '发动机水温过高报警_ocr', '发动机水温过高', '')
        """
        if "（" or "：" in value:
            value = value.replace("（", "(").replace("）", ")").replace("：", ":")
        for attr in self.__class__.__dict__:
            if str(attr).startswith("Pattern"):
                pat = eval(f"self.{attr}")
                result = pat.match(value.strip())
                if result:
                    return tuple([attr[len("Pattern"):]] + list(result.groups()))
        logger.warning(f"step can not be parsed: {value}, maybe it's just a comment or you need to add some rules to parse this new type of step")

    def parse_to_code(self, value: (str, list, tuple)):
        """
        parse steps/preconditions/expectations to code
        @param:
            value: one or a serial of steps
        @return:
            list: a list of code lines
        @example:
            "('Battery', 'ON', '')" -> "API.ps.power_on()"
            "('KL15', 'ON', '')" -> "API.kl15('on')"
            "('VehicleConfig', 'ENGINE_CONTROL_UNIT', '00001', '(发动机控制单元)')" -> "API.set_vehicle_config("ENGINE_CONTROL_UNIT", "00001")"
            "('Wait', '5000', '')" -> "API.wait(500)"
            "('SendMsg', '0x371', 'EngClntTempWarn', '0', '')" -> "API.send("0x371", "EngClntTempWarn", '0')"
        """
        if isinstance(value, str):
            value = [value]
        if not value:
            logger.warning(f"there's no code pattern to be parsed.")
            return []

        new_value = []
        for item in value:
            if item is not None:
                params = item[1:]
                codes = eval(f'self.Code.{item[0].lower()}(*{params})')
                if isinstance(codes, str):
                    new_value.append(codes)
                elif isinstance(codes, (list, tuple)):
                    new_value.extend(codes)

        return new_value


Pattern = _Pattern()
