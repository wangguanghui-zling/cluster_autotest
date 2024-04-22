from common import logger
import allure
import sys
import pytest
from api import API


class TestTell1:
    def setup_class(self):
        logger.info(f"{'=' * 30} class setup {'=' * 30}")
        API.reset_measurement()
        API.reset_battery()

    def teardown_class(self):
        logger.info(f"{'=' * 30} class teardown {'=' * 30}")
        # API.close()

    def setup_method(self, method):
        logger.info(f"{'*' * 10} method setup: {method.__name__} {'*' * 10}")

    def teardown_method(self, method):
        logger.info(f"{'*' * 10} method teardown: {method.__name__} {'*' * 10}")
        API.reset_battery()
        API.reset_signals()

    @allure.id("TC_Telltale_Position_indicator_working_indicator_001")
    @allure.title("TC_Telltale_Position_indicator_working_indicator_001(位置灯工作指示灯(配置智能保险盒或者CEM))")
    @allure.description(
        """
        TestId:
            TC_Telltale_Position_indicator_working_indicator_001
        TestTitle:
            位置灯工作指示灯(配置智能保险盒或者CEM)
        TestDescription:
            位置灯工作指示灯_基本功能
        TestPrecondition:
            BAT ON
            KL15 ON
        TestStep:
            1.Send 0x19C:PosnLmpOutpSts_R_Pbox=0
        TestExpectation:
            位置灯工作指示灯熄灭
        TestType:
            HMI
        TestTag:
            A02
        TestPriority:
            P1
        """
    )
    @allure.tag(*['A02'])
    def test_TC_Telltale_Position_indicator_working_indicator_001(self):
        logger.info(">>>test preconditions:")
        API.battery('ON')  # 
        API.kl15("on")  # 

        logger.info(">>>test steps:")
        API.send("0x19C", "PosnLmpOutpSts_R_Pbox", "0")  # 

        logger.info(">>>test assert:")

    @allure.id("TC_Telltale_Position_indicator_working_indicator_002")
    @allure.title("TC_Telltale_Position_indicator_working_indicator_002(位置灯工作指示灯(配置智能保险盒或者CEM))")
    @allure.description(
        """
        TestId:
            TC_Telltale_Position_indicator_working_indicator_002
        TestTitle:
            位置灯工作指示灯(配置智能保险盒或者CEM)
        TestDescription:
            位置灯工作指示灯_基本功能
        TestPrecondition:
            BAT ON
            IGN ON
            默认配置
        TestStep:
            1.Send 0x19C:PosnLmpOutpSts_R_Pbox=1
        TestExpectation:
            位置灯工作指示灯点亮
        TestType:
            HMI
        TestTag:
            A02
        TestPriority:
            P2
        """
    )
    @allure.tag(*['A02'])
    def test_TC_Telltale_Position_indicator_working_indicator_002(self):
        logger.info(">>>test preconditions:")
        API.battery('ON')  # 
        API.kl15("on")  # 

        logger.info(">>>test steps:")
        API.send("0x19C", "PosnLmpOutpSts_R_Pbox", "1")  # 

        logger.info(">>>test assert:")

    @allure.id("TC_Telltale_Position_indicator_working_indicator_003")
    @allure.title("TC_Telltale_Position_indicator_working_indicator_003(位置灯工作指示灯(配置智能保险盒或者CEM))")
    @allure.description(
        """
        TestId:
            TC_Telltale_Position_indicator_working_indicator_003
        TestTitle:
            位置灯工作指示灯(配置智能保险盒或者CEM)
        TestDescription:
            位置灯工作指示灯_基本功能
        TestPrecondition:
            BAT ON
            IGN ON
            默认配置
        TestStep:
            1.Send 0x19C:PosnLmpOutpSts_R_Pbox=0
            2.Send 0x19C:PosnLmpOutpSts_R_Pbox=1
            3.Send 0x19C:PosnLmpOutpSts_R_Pbox=0
        TestExpectation:
            1.位置灯工作指示灯熄灭
            2.位置灯工作指示灯点亮
            3.位置灯工作指示灯熄灭
        TestType:
            HMI
        TestTag:
            A02
        TestPriority:
            P3
        """
    )
    @allure.tag(*['A02'])
    def test_TC_Telltale_Position_indicator_working_indicator_003(self):
        logger.info(">>>test preconditions:")
        API.battery('ON')  # 
        API.kl15("on")  # 

        logger.info(">>>test steps:")
        API.send("0x19C", "PosnLmpOutpSts_R_Pbox", "0")  # 
        API.send("0x19C", "PosnLmpOutpSts_R_Pbox", "1")  # 
        API.send("0x19C", "PosnLmpOutpSts_R_Pbox", "0")  # 

        logger.info(">>>test assert:")

