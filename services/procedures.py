import inspect
import logging
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import TimeoutException
from services.exceptions import FindElementFailedException
from services.webdriver import WebDriver
from services.driver_wait import DriverWait
from services.find_elements import FindElement, locator
from services.scroll import Scroll

logger = logging.getLogger()


class Procedures(object):
    class_variables = {}

    def __init__(self, contents, key=None, proxy=None):
        self.contents = contents
        self.key = key
        self.proxy = proxy

    def _open(self, browser, url):
        driver = WebDriver(self.proxy, browser).driver()
        driver.set_window_size(1366, 768)
        self.class_variables[self.key]['driver'] = driver
        driver.get(url)

    @staticmethod
    def _wait(strategy, duration, driver=None, class_name=None, *condition):
        try:
            DriverWait(strategy, duration, driver, class_name,
                       *condition).wait()
        except TimeoutException:
            logger.error("find element failed, {} {}".format(
                class_name, condition))
            raise FindElementFailedException(
                "find element failed, {} {}".format(class_name, condition))

    def _input(self, strategy, ele_value, input_value):
        driver = self.class_variables.get(self.key).get('driver')
        ele = FindElement(driver, strategy, ele_value).find_element()
        ele.clear()
        ele.send_keys(input_value)

    def _click(self, strategy, ele_value):
        driver = self.class_variables.get(self.key).get('driver')
        ele = FindElement(driver, strategy, ele_value).find_element()
        ele.click()

    def _scroll(self, strategy, abscissa, ordinate):
        driver = self.class_variables.get(self.key).get('driver')
        Scroll(driver, strategy, abscissa, ordinate).scroll()

    def _close(self):
        driver = self.class_variables.get(self.key).get('driver')
        driver.quit()

    def parse(self):
        for content in self.contents:
            action = content.get('action')
            if action == 'open_browser':
                self._open(content.get('browser'), content.get('input'))
            elif action == 'wait':
                strategy = content.get('strategy')
                duration = content.get('duration')
                if strategy == 'sleep':
                    self._wait(strategy, duration)
                else:
                    class_name = content.get('expected_condition')
                    args = inspect.getfullargspec(
                        getattr(expected_conditions, class_name)).args[1:]
                    first_args = args[0]
                    driver = self.class_variables.get(self.key).get('driver')
                    if first_args == 'locator':
                        locator_strategy = locator.get(
                            content.get('locator_strategy'))
                        new_locator = (locator_strategy,
                                       content.get('locator_value'))
                        if len(args) == 1:
                            self._wait(strategy, duration, driver,
                                       content.get('expected_condition'),
                                       new_locator)
                        elif len(args) > 1:
                            self._wait(strategy, duration, driver,
                                       content.get('expected_condition'),
                                       new_locator,
                                       content.get('expected_value'))
                    elif first_args == 'element':
                        ele = FindElement(driver,
                                          content.get('locator_strategy'),
                                          content.get('locator_value'))
                        if len(args) == 1:
                            self._wait(strategy, duration, driver,
                                       content.get('expected_condition'), ele)
                        elif len(args) > 1:
                            self._wait(strategy, duration, driver,
                                       content.get('expected_condition'), ele,
                                       content.get('expected_value'))
                    else:
                        self._wait(strategy, duration, driver,
                                   content.get('expected_condition'),
                                   content.get('expected_value'))
            elif action == 'input':
                self._input(
                    content.get('locator_strategy'),
                    content.get('locator_value'), content.get('input'))
            elif action == 'click':
                self._click(
                    content.get('locator_strategy'),
                    content.get('locator_value'))
            elif action == 'scroll':
                self._scroll(
                    content.get('strategy'), content.get('locator_strategy'),
                    content.get('locator_value'))
            elif action == 'close_browser':
                self._close()
