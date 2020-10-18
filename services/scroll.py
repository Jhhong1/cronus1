import logging
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from services.find_elements import locator


logger = logging.getLogger()


class Scroll(object):
    def __init__(self, driver, strategy, abscissa, ordinate):
        """
        :param driver: WebDriver object
        :param strategy: scroll strategy, should be scrollBy or scrollIntoView
        :param abscissa: abscissa or set of supported locator strategies
        :param ordinate: ordinate or value to use when finding elements
        """
        self.driver = driver
        self.strategy = strategy
        self.abscissa = abscissa
        self.ordinate = ordinate

    def scroll_by(self):
        logger.info('window.scrollBy({},{})'.format(self.abscissa, self.ordinate))
        return self.driver.execute_script('window.scrollBy({},{})'.format(self.abscissa, self.ordinate))

    def scroll_into_view(self):
        locator_obj = locator.get(self.abscissa)
        ele = WebDriverWait(self.driver, 20).until(expected_conditions.visibility_of_element_located((locator_obj,
                                                                                                      self.ordinate)))
        return self.driver.execute_script("arguments[0].scrollIntoView();", ele)

    def scroll(self):
        assert self.strategy in ('scroll_by', 'scroll_into_view'), "support scroll strategies is not scrollBy or " \
                                                                "scrollIntoView"
        data = {
            'scroll_by': self.scroll_by,
            'scroll_into_view': self.scroll_into_view
        }
        return data[self.strategy]()
