# -*- coding: utf-8 -*-

"""Main module."""

import os

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


LOGIN_URL = "https://my.chevrolet.com/login"
USER_FIELD = "Login_Username"
PASS_FIELD = "Login_Password"
LOGIN_BUTTON = "Login_Button"
DEFAULT_DRIVER = "/usr/local/bin/chromedriver"
TIMEOUT = 120

class EVCar(object):

    def __init__(self, est_range=0, mileage=0, plugged_in=False,
                 state="", charge_percent=0, eta=0, charge_mode="",
                 charging=""):
        super(EVCar, self).__init__()
        self.plugged_in = plugged_in
        self.range = est_range
        self.percent = charge_percent
        self.mileage = mileage
        self.eta = eta
        self.state = state
        self.charge_mode = charge_mode
        self.charging = charging

    def __str__(self):
        return ("<EVCar range=%s miles, bat=%s%%, plugged_in=%s, "
                "mileage=%s miles, charging=%s, charge_mode=%s, eta=%s, "
                "state=%s>" % (
                    self.range, self.percent, self.plugged_in, self.mileage,
                    self.charging, self.charge_mode, self.eta, self.state)
        )


class MyChevy(object):

    def __init__(self, user, passwd, driver=DEFAULT_DRIVER, headless=True):
        super(MyChevy, self).__init__()

        self.chromedriver = driver
        self.user = user
        self.passwd = passwd
        self.headless = headless

    def parse_plug(self, driver):
        status = driver.find_element_by_css_selector(".status-right").text.split("\n")
        charging = status[0]

        if "Plugged in" in charging:
            plugged_in = True
        else:
            plugged_in = False

        state = charging

        return (plugged_in, state)

    def charging(self, driver):
        status = driver.find_element_by_css_selector(".status-right").text.split("\n")
        mode = status[1]
        return mode

    def range(self, driver):
        status = driver.find_element_by_css_selector(".status-right").text.split("\n")
        for i, key in enumerate(status):
            if "Estimated Electric Range" in key:
                # strip out units
                return int(status[i + 1].split(' ')[0])

    def eta(self, driver):
        status = driver.find_element_by_css_selector(".status-right").text.split("\n")
        for i, key in enumerate(status):
            if "Estimated Full Charge" in key:
                # strip out units
                return status[i + 1]

    def charge_mode(self, driver):
        status = driver.find_element_by_css_selector(".status-right").text.split("\n")
        for i, key in enumerate(status):
            if "Charge Mode" in key:
                # strip out units
                return status[i + 1]

    def mileage(self, driver):
        mileage = driver.find_element_by_css_selector(
            ".panel-vehicle-info-table tbody tr:nth-child(1) td:nth-child(2)").text
        mileage = mileage.replace(',', '')
        return int(mileage)

    def _load_page(self, driver):
        driver.get(LOGIN_URL)

        # Login as user
        user = driver.find_element_by_id(USER_FIELD)
        passwd = driver.find_element_by_id(PASS_FIELD)
        user.send_keys(self.user)
        passwd.send_keys(self.passwd)
        driver.find_element_by_id(LOGIN_BUTTON).click()

        # try, though wait for up to TIMEOUT seconds

        element_present = EC.presence_of_element_located(
            (By.CLASS_NAME, 'status-box'))
        WebDriverWait(driver, TIMEOUT).until(element_present)

    def data(self):
        # Get the main page
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(
            executable_path=os.path.abspath(self.chromedriver),
            chrome_options=chrome_options)

        self._load_page(driver)

        # Start pulling out data
        charge = driver.find_element_by_css_selector(".status-box h1").text
        charge = int(charge.replace('%', ''))
        car = EVCar(charge_percent=charge)

        plugged_in, state = self.parse_plug(driver)
        car.plugged_in = plugged_in
        car.state = state

        car.charge_mode = self.charge_mode(driver)
        car.charging = self.charging(driver)
        car.eta = self.eta(driver)
        car.range = self.range(driver)
        car.charge_mode = self.charge_mode(driver)
        car.mileage = self.mileage(driver)

        # if we aren't headless, don't close the window at the end
        if self.headless is True:
            driver.close()
        else:
            self.driver = driver

        return car
