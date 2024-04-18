#! /usr/bin/env python



"""
this module process each column of test case independently and create one class for each column
"""

from common.tc.conf import Pattern
import re


def remove_index(value: (str, list, tuple)):
    """
    delete index number at the front of step/expectation/precondition/..., for example: passed in "1.abc", return "abc"
    @param:
        value: mostly step/expectation/precondition
    @return:
        str or list
    """
    def remove(val: str):
        if '.' in val:
            index_str = val.split('.')[0]
            try:
                int(index_str)
            except ValueError:
                return val
            else:
                return val[len(index_str) + 1:]
        return val

    if isinstance(value, str):
        return remove(value)
    else:
        result = []
        for v in value:
            result.append(remove(v))
        return result


class _Base:
    """
    base class
    """
    def __init__(self, value: (str, list, tuple, dict)):
        if isinstance(value, dict):
            self.value = "_".join([str(y) for x, y in value.items()])
        elif isinstance(value, (list, tuple)):
            self.value = "_".join(value)
        else:
            self.value = value


class TestId(_Base):

    PatternReplace = re.compile(r"[-\s]")

    def __init__(self, value: str, delimiter: str = None):
        super(TestId, self).__init__(value)
        self.value = self.PatternReplace.sub("_", self.value)


class TestTitle(_Base):
    def __init__(self, value: (str, list, tuple), delimiter: str = None):
        super(TestTitle, self).__init__(value)


class TestDescription:
    def __init__(self, value: (str, list, tuple), delimiter: str = "\n"):
        if isinstance(value, (list, tuple)):
            self.value = value
        else:
            if delimiter in value:
                self.value = value.split(delimiter)
            else:
                self.value = [value]


class TestPrecondition(TestDescription):
    def __init__(self, value: (str, list, tuple), delimiter: str = "\n"):
        super(TestPrecondition, self).__init__(value, delimiter)
        tmp_value_list = remove_index(self.value)
        self.value = []
        insert_index = -1
        vehicle_config = ["vehicleconfig"]
        for index, step in enumerate(tmp_value_list):
            step_tuple = Pattern.parser(step)
            if step_tuple and str(step_tuple[0]).lower() == "vehicleconfig":
                if insert_index == -1:
                    insert_index = index
                vehicle_config.append(step_tuple[1:])
            else:
                self.value.append(step_tuple)
        if len(vehicle_config) > 1:
            if insert_index == -1:
                self.value.append(vehicle_config)
            else:
                self.value.insert(insert_index, vehicle_config)


class TestStep(TestDescription):
    def __init__(self, value: (str, list, tuple), delimiter: str = "\n"):
        super(TestStep, self).__init__(value, delimiter)
        tmp_value_list = remove_index(self.value)
        self.value = []
        for step in tmp_value_list:
            step_tuple = Pattern.parser(step)
            if step_tuple and str(step_tuple[0]).lower() == "vehicleconfig":
                self.value.append(["vehicleconfig", step_tuple[1:]])
            else:
                self.value.append(step_tuple)


class TestExpectation(TestStep):
    def __init__(self, value: (str, list, tuple), delimiter: str = "\n"):
        super(TestExpectation, self).__init__(value, delimiter)


class TestType(_Base):
    def __init__(self, value: str, delimiter: str = None):
        super(TestType, self).__init__(value)


class TestPlatform:
    pass


class TestProject:
    pass


class TestCaseStatus(_Base):
    def __init__(self, value: str, delimiter: str = None):
        super(TestCaseStatus, self).__init__(value)


class TestTag(TestDescription):
    def __init__(self, value: (str, list, tuple), delimiter: str = ","):
        super(TestTag, self).__init__(value, delimiter)
        self.value = [x.strip() for x in self.value if x]


class TestPriority(_Base):
    def __init__(self, value: str, delimiter: str = None):
        super(TestPriority, self).__init__(value)


class TestSeverity:
    pass


class TestSuite:
    pass


class TestEpic:
    pass


class TestStory:
    pass


class TestFeature:
    pass


class TestRequirement(TestDescription):
    def __init__(self, value: (str, list, tuple), delimiter: str = "\n"):
        super(TestRequirement, self).__init__(value, delimiter)


class TestComment(TestDescription):
    def __init__(self, value: (str, list, tuple), delimiter: str = "\n"):
        super(TestComment, self).__init__(value, delimiter)


class TestResult:
    pass


class TestJiraId(TestDescription):
    def __init__(self, value: (str, list, tuple), delimiter: str = "\n"):
        super(TestJiraId, self).__init__(value, delimiter)


class TestIssue:
    pass


class TestOperator:
    pass


class TestDateTime:
    pass


if __name__ == "__main__":
    print(Pattern.parser("OCR_发动机水温过高报警_ocr=发动机水温过高"))
