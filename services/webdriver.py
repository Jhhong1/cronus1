import os
import logging
from selenium import webdriver
from selenium.webdriver.common.proxy import Proxy
from selenium.webdriver import FirefoxProfile

logger = logging.getLogger()


class WebDriver(object):

    def __init__(self, proxy=None, browser='chrome'):
        self.proxy = proxy
        self.browser = browser
        self.model = os.getenv('RUN_MODEL', 'docker')

    def _proxy(self):
        logger.info("proxy: {}".format(self.proxy))
        if self.proxy and isinstance(self.proxy,
                                     dict) and self.browser == 'chrome':
            proxy = Proxy()
            for k, v in self.proxy.items():
                proxy.__setattr__(k, v)
            capabilities = webdriver.DesiredCapabilities.CHROME
            proxy.add_to_capabilities(capabilities)
            return capabilities
        elif self.proxy and isinstance(self.proxy,
                                       dict) and self.browser == 'firefox':
            profile = FirefoxProfile()
            profile.set_preference('network.proxy.type', 1)
            for k, v in self.proxy.items():
                scheme = k.split("_")
                host_details = v.split(":")
                if len(scheme) > 1 and len(host_details) > 1:
                    profile.set_preference("network.proxy.%s" % scheme[0],
                                           host_details[0])
                    profile.set_preference("network.proxy.%s_port" % scheme[0],
                                           int(host_details[1]))
            profile.update_preferences()
            # profile.accept_untrusted_certs = True
            return profile

    def chrome(self):
        options = webdriver.ChromeOptions()
        options.add_argument('ignore-certificate-errors')
        options.add_argument('headless')
        options.add_argument('no-sandbox')
        if self.model == 'docker':
            if self.proxy:
                return webdriver.Chrome(
                    desired_capabilities=self._proxy(), chrome_options=options)
            return webdriver.Chrome(chrome_options=options)
        else:
            current_path = os.path.join(os.getcwd(), 'chromedriver')
            if self.proxy:
                return webdriver.Chrome(
                    executable_path=current_path,
                    desired_capabilities=self._proxy(),
                    chrome_options=options)
            return webdriver.Chrome(
                executable_path=current_path, chrome_options=options)

    def firefox(self):
        if self.model == 'docker':
            options = webdriver.FirefoxOptions()
            options.add_argument('--headless')
            if self.proxy:
                return webdriver.Firefox(
                    firefox_profile=self._proxy(), firefox_options=options)
            return webdriver.Firefox(firefox_options=options)
        else:
            current_path = os.path.join(os.getcwd(), 'geckodriver')
            if self.proxy:
                return webdriver.Firefox(
                    firefox_profile=self._proxy(), executable_path=current_path)
            return webdriver.Firefox(executable_path=current_path)

    def driver(self):
        assert self.browser in (
            'chrome', 'firefox'), 'The browser is not Google or Firefox'
        if self.browser == 'chrome':
            return self.chrome()
        else:
            return self.firefox()
