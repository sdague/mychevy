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
                 charge_volts=0, charge_percent=0, eta=0):
        super(EVCar, self).__init__()
        self.plugged_in = plugged_in
        self.range = est_range
        self.volts = charge_volts
        self.percent = charge_percent
        self.mileage = mileage
        self.eta = eta

    def __str__(self):
        return ("<EVCar range=%s miles, bat=%s%%, plugged_in=%s, "
                "mileage=%s miles>" % (
                    self.range, self.percent, self.plugged_in, self.mileage))


class MyChevy(object):

    def __init__(self, user, passwd, driver=DEFAULT_DRIVER, headless=True):
        super(MyChevy, self).__init__()

        self.chromedriver = driver
        self.user = user
        self.passwd = passwd

        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        self.driver = webdriver.Chrome(
            executable_path=os.path.abspath(self.chromedriver),
            chrome_options=chrome_options)

    async def data(self):
        # Get the main page
        driver = self.driver
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
        charge = driver.find_element_by_css_selector(".status-box h1").text
        charge = charge.replace('%', '')

        status_r = driver.find_element_by_css_selector(".status-right").text.split("\n")
        charging = status_r[0]

        if "Plugged in" in charging:
            plugged_in = True
        else:
            plugged_in = False

        car = EVCar(plugged_in=plugged_in, charge_percent=charge)

        for i, key in enumerate(status_r):
            if "Estimated Electric Range" in key:
                # strip out units
                car.range = status_r[i + 1].split(' ')[0]

        car.mileage = driver.find_element_by_css_selector(
            ".panel-vehicle-info-table tbody tr:nth-child(1) td:nth-child(2)").text

        return car
