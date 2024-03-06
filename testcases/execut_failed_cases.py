import os
import functools

def execut_failed_cases(func):
    """
    自定义装饰器，用于
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            # 执行测试用例
            func(*args, **kwargs)
        except AssertionError:
            test_name = func.__name__  # 获取测试用例名称
            print(test_name)

    return wrapper