from selenium.webdriver.common.by import By


locator = {
    'by_id': By.ID,
    'by_name': By.NAME,
    'by_class_name': By.CLASS_NAME,
    'by_tag_name': By.TAG_NAME,
    'by_link_text': By.LINK_TEXT,
    'by_partial_link_text': By.PARTIAL_LINK_TEXT,
    'by_xpath': By.XPATH,
    'by_css_selector': By.CSS_SELECTOR
}


class FindElement(object):
    def __init__(self, driver, strategy, value):
        """
        :param driver: WebDriver object, type(object)
        :param strategy: locator strategies， type(string)
        :param value: value to use when finding elements, type(string)
        """
        self.driver = driver
        self.strategy = strategy
        self.value = value

    def find_element(self):
        assert self.strategy in locator, "locator strategies not supported"
        return self.driver.find_element(locator.get(self.strategy), self.value)

    def find_elements(self):
        assert self.strategy in locator, "locator strategies not supported"
        return self.driver.find_elements(locator.get(self.strategy), self.value)
