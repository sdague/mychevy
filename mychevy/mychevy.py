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
import time

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
EVSTATS_URL = "https://my.chevrolet.com/vehicleProfile/{0}/{1}/evstats?cb={2}.{3}"

USER_AGENT = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) "
              "AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/42.0.2311.90 Safari/537.36")

# b'{"messages":[],"serverErrorMsgs":[],"data":{"dataAsOfDate":1517317946000,"batteryLevel":82,"chargeState":"not_charging","plugState":"unplugged","rateType":"PEAK","voltage":0,"electricRange":155,"totalRange":182,"chargeMode":"DEPARTURE_BASED","electricMiles":1843,"gasMiles":0,"totalMiles":1843,"percentageOnElectric":1,"fuelEconomy":1000,"electricEconomy":44,"combinedEconomy":9,"fuelUsed":182,"electricityUsed":182,"estimatedGallonsFuelSaved":70.45,"estimatedCO2Avoided":1366.73,"estimatedFullChargeBy":"5:00
# a.m."}}'


class ServerError(Exception):
    pass


CAR_ATTRS = ("chargeMode", "chargeState",
             "batteryLevel", "electricRange",
             "totalRange", "totalMiles", "electricMiles",
             "gasMiles", "voltage", "estimatedFullChargeBy")


class EVCar(object):

    def __init__(self, car):
        super(EVCar, self).__init__()
        self.vin = car["vin"]
        self.vid = car["vehicle_id"]
        self.onstar = car["onstarAccountNumber"]
        self.year = car["year"]
        self.make = car["make"]
        self.model = car["model"]
        self.img = car["imageUrl"]

        # computed binaries
        self.plugged_in = False

        # car stats that we'll update later
        self.chargeMode = ""
        self.batteryLevel = ""
        self.chargeState = ""
        self.electricRange = 0
        self.totalRange = 0
        self.totalMiles = 0
        self.electricMiles = 0
        self.gasMiles = 0
        self.voltage = 0
        self.estimatedFullChargeBy = ""

    @property
    def name(self):
        return "{0} {1} {2}".format(self.year, self.make, self.model)

    def update(self, *args, **kwargs):
        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                raise KeyError("No attribute named %s" % k)

    def from_json(self, data):
        try:
            res = json.loads(data.decode('utf-8'))

            # I've never actually seen serverErrorMsgs, but allow for them
            if res["serverErrorMsgs"] or type(res["data"]) == str:
                raise ServerError(res)

            d = res["data"]

            self.plugged_in = (d['plugState'] == "plugged")

            for a in CAR_ATTRS:
                setattr(self, a, d[a])

        except json.JSONDecodeError:
            _LOGGER.exception("Failure to decode json: %s" % data)
        except KeyError as e:
            _LOGGER.exception("Expected key not found")

    def __str__(self):
        return ("<EVCar name=%s, totalRange=%s miles, batteryLevel=%s%%, "
                "plugged_in=%s, "
                "totalMiles=%s miles, chargeState=%s, chargeMode=%s, "
                "estimatedFullChargeBy=%s>" % (
                    self.name, self.totalRange, self.batteryLevel,
                    self.plugged_in, self.totalMiles, self.chargeState,
                    self.chargeMode, self.estimatedFullChargeBy))


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
            _LOGGER.debug("Vehicles: %s", data['data']['vehicleMap'])
            for vid, vehicle in data['data']['vehicleMap'].items():
                self.cars.append(EVCar(vehicle))
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
            now = int(round(time.time() * 1000))
            url = EVSTATS_URL.format(c.vin, c.onstar, now, 15258643512040)
            res = requests.get(url, headers=headers,
                               cookies=self.cookies, allow_redirects=False)
            c.from_json(res.content)
        return self.cars
