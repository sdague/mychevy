# Copyright 2017 Sean Dague
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""Main module."""

import json
import logging
import os

import requests

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


_LOGGER = logging.getLogger(__name__)

LOGIN_URL = "https://my.chevrolet.com/login"
USER_FIELD = "Login_Username"
PASS_FIELD = "Login_Password"
LOGIN_BUTTON = "Login_Button"
DEFAULT_DRIVER = "/usr/local/bin/chromedriver"
TIMEOUT = 120

SUCCESS_URL = "https://my.chevrolet.com/init/loginSuccessData"
EVSTATS_URL = "https://my.chevrolet.com/vehicleProfile/{0}/{1}/evstats"

USER_AGENT = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) "
              "AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/42.0.2311.90 Safari/537.36")

# b'{"messages":[],"serverErrorMsgs":[],"data":{"dataAsOfDate":1517317946000,"batteryLevel":82,"chargeState":"not_charging","plugState":"unplugged","rateType":"PEAK","voltage":0,"electricRange":155,"totalRange":182,"chargeMode":"DEPARTURE_BASED","electricMiles":1843,"gasMiles":0,"totalMiles":1843,"percentageOnElectric":1,"fuelEconomy":1000,"electricEconomy":44,"combinedEconomy":9,"fuelUsed":182,"electricityUsed":182,"estimatedGallonsFuelSaved":70.45,"estimatedCO2Avoided":1366.73,"estimatedFullChargeBy":"5:00
# a.m."}}'


class ServerError(Exception):
    pass


class EVCar(object):

    def __init__(self, est_range=0, mileage=0, plugged_in=False,
                 state="", charge_percent=0, eta=0, charge_mode="",
                 charging="", vin="", onstar=""):
        super(EVCar, self).__init__()
        self.plugged_in = plugged_in
        self.range = est_range
        self.percent = charge_percent
        self.mileage = mileage
        self.eta = eta
        self.state = state
        self.charge_mode = charge_mode
        self.charging = charging
        self.vin = vin
        self.onstar = onstar

    def update(self, *args, **kwargs):
        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                raise KeyError("No attribute named %s" % k)

    def from_json(self, data):
        try:
            res = json.loads(data)

            # I've never actually seen serverErrorMsgs, but allow for them
            if res["serverErrorMsgs"] or type(res["data"]) == str:
                raise ServerError(res)

            d = res["data"]
            self.charge_mode = d['chargeMode']
            self.percent = d['batteryLevel']
            self.plugged_in = (d['plugState'] == "plugged")
            self.charging = d['chargeState']
            self.range = d['electricRange']
            self.mileage = d['totalMiles']
        except json.decoder.JSONDecodeError:
            _LOGGER.exception("Failure to decode json: %s" % data)
        except KeyError as e:
            _LOGGER.exception("Expected key not found")

    def __str__(self):
        return ("<EVCar vin=%s, range=%s miles, bat=%s%%, plugged_in=%s, "
                "mileage=%s miles, charging=%s, charge_mode=%s, eta=%s, "
                "state=%s>" % (
                    self.vin, self.range, self.percent, self.plugged_in,
                    self.mileage,
                    self.charging, self.charge_mode, self.eta, self.state))


class MyChevy(object):

    def __init__(self, user, passwd, driver=DEFAULT_DRIVER, headless=True):
        super(MyChevy, self).__init__()

        self.chromedriver = driver
        self.user = user
        self.passwd = passwd
        self.headless = headless
        self.cars = []
        self.cookies = None

    def login(self):
        """New login path, to be used with json data path."""
        # Get the main page
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")

        driver = webdriver.Chrome(
            executable_path=os.path.abspath(self.chromedriver),
            chrome_options=chrome_options)

        driver.get(LOGIN_URL)
        # Login as user
        user = driver.find_element_by_id(USER_FIELD)
        passwd = driver.find_element_by_id(PASS_FIELD)
        user.send_keys(self.user)
        passwd.send_keys(self.passwd)
        driver.find_element_by_id(LOGIN_BUTTON).click()

        # wait for any cars to show up...
        element_present = EC.presence_of_element_located(
            (By.CLASS_NAME, 'panel-vehicle-display-snapshot'))
        WebDriverWait(driver, TIMEOUT).until(element_present)

        self.cookies = {}
        for cookie in driver.get_cookies():
            c = {cookie['name']: cookie['value']}
            self.cookies.update(c)

    def get_cars(self):
        headers = {"user-agent": USER_AGENT}
        res = requests.get(SUCCESS_URL, headers=headers,
                           cookies=self.cookies, allow_redirects=False)
        try:
            data = json.loads(res.content)
            if data["serverErrorMsgs"]:
                raise Exception(data["serverErrorMsgs"])

            self.cars = []
            for vehicle in data['data']['vehicles']:
                self.cars.append(
                    EVCar(vin=vehicle['vin'],
                          onstar=vehicle['onstarAccountNumber']))
        except Exception:
            raise Exception("""
Something went wrong!

Cookies: %s

Content: %s

Location: %s
            """ % (self.cookies, res.content, res.history))

    def update_cars(self):
        headers = {"user-agent": USER_AGENT}
        for c in self.cars:
            url = EVSTATS_URL.format(c.vin, c.onstar)
            res = requests.get(url, headers=headers,
                               cookies=self.cookies, allow_redirects=False)
            c.from_json(res.content)
        return self.cars
