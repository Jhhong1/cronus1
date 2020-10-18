from time import sleep
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions


class DriverWait(object):
    def __init__(self, strategy, duration, driver=None, class_name=None, *condition):
        """
        :param strategy: wait strategies，type(string)
        :param duration: length of wait, type(int)
        :param class_name: class name in expected_conditions module, type(string)
        :param condition: args of expected_conditions. locator: used to find the element;
        element: the WebElement; text: text
        """
        self.strategy = strategy
        self.duration = duration
        self.driver = driver
        self.class_name = class_name
        self.condition = condition

    def forced_wait(self):
        return sleep(self.duration)

    def driver_wait(self):
        class_name = getattr(expected_conditions, self.class_name)
        return WebDriverWait(self.driver, self.duration).until(class_name(*self.condition))

    def wait(self):
        assert self.strategy in ('sleep', 'explicit'), "supported strategies should be 'sleep' or 'explicit'"
        data = {
            'sleep': self.forced_wait,
            'explicit': self.driver_wait
        }
        return data[self.strategy]()
