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

from functools import wraps
import json
import logging
import re
import time
import urllib

import requests

_LOGGER = logging.getLogger(__name__)

TIMEOUT = 120
KEY = 15258643512041

LOGIN_URL = "https://custlogin.gm.com/gmb2cprod.onmicrosoft.com/B2C_1A_SeamlessMigration_SignUpOrSignIn/SelfAsserted?tx={}&p=B2C_1A_SeamlessMigration_SignUpOrSignIn"  # noqa
TOKEN_URL = "https://custlogin.gm.com/gmb2cprod.onmicrosoft.com/B2C_1A_SeamlessMigration_SignUpOrSignIn/api/CombinedSigninAndSignup/confirmed?csrf_token={}&tx={}&p=B2C_1A_SeamlessMigration_SignUpOrSignIn"  # noqa

URLS = {
    "us": {
        "success": "https://my.chevrolet.com/init/loginSuccessData",
        "oc_login": "https://my.chevrolet.com/oc_login",
        "loginSuccessData": "https://my.chevrolet.com/api/init/loginSuccessData",
        "home": "https://my.chevrolet.com/home",
        "login": "https://my.chevrolet.com/oc_login",
        "evstats": (
            "https://my.chevrolet.com/api/vehicleProfile/"
            "{0}/{1}/evstats/false?cb={2}.{3}"
        ),
        "session": (
            "https://my.chevrolet.com/vehicleProfile/"
            "{0}/{1}/createAppSessionKey?cb={2}.{3}"
        ),
    },
    "ca": {
        "success": "https://my.gm.ca/chevrolet/en/init/loginSuccessData",
        "home": "https://my.gm.ca/gm/en/home",
        "oc_login": "https://my.gm.ca/gm/en/oc_login",
        "loginSuccessData": "https://my.gm.ca/gm/en/api/init/loginSuccessData",
        "login": "https://my.gm.ca/chevrolet/en/oc_login",
        "evstats": (
            "https://my.gm.ca/chevrolet/en/api/vehicleProfile/"
            "{0}/{1}/evstats/false?cb={2}.{3}"
        ),
        "session": (
            "https://my.gm.ca/chevrolet/en/api/vehicleProfile/"
            "{0}/{1}/createAppSessionKey?cb={2}.{3}"
        ),
    },
}


def get_url(kind="", country="us"):
    return URLS[country][kind]


settings_json_re = re.compile("var SETTINGS = ({.*})")
id_token_re = re.compile("name='id_token'.*value='(.*)'/>")


USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/75.0.3770.80 Safari/537.36"
)

# b'{"messages":[],"serverErrorMsgs":[],"data":{"dataAsOfDate":1517317946000,"batteryLevel":82,"chargeState":"not_charging","plugState":"unplugged","rateType":"PEAK","voltage":0,"electricRange":155,"totalRange":182,"chargeMode":"DEPARTURE_BASED","electricMiles":1843,"gasMiles":0,"totalMiles":1843,"percentageOnElectric":1,"fuelEconomy":1000,"electricEconomy":44,"combinedEconomy":9,"fuelUsed":182,"electricityUsed":182,"estimatedGallonsFuelSaved":70.45,"estimatedCO2Avoided":1366.73,"estimatedFullChargeBy":"5:00
# a.m."}}'


class ServerError(Exception):
    pass


CAR_ATTRS = (
    "chargeMode",
    "chargeState",
    "batteryLevel",
    "electricRange",
    "totalRange",
    "totalMiles",
    "electricMiles",
    "gasRange",
    "gasFuelLevelPercentage",
    "fuelEconomy",
    "gasMiles",
    "voltage",
    "estimatedFullChargeBy",
)


def retry(exceptions, tries=3, delay=3, backoff=2, logger=None):
    """
    Retry calling the decorated function using an exponential backoff.

    Args:
        exceptions: The exception to check. may be a tuple of
            exceptions to check.
        tries: Number of times to try (not retry) before giving up.
        delay: Initial delay between retries in seconds.
        backoff: Backoff multiplier (e.g. value of 2 will double the delay
            each retry).
        logger: Logger to use. If None, print.
    """

    def deco_retry(f):
        @wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                except exceptions as e:
                    msg = "{}, Retrying in {} seconds...".format(e, mdelay)
                    if logger:
                        logger.warning(msg)
                    else:
                        print(msg)
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return f(*args, **kwargs)

        return f_retry  # true decorator

    return deco_retry


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
        self.fuelEconomy = 0
        self.batteryLevel = ""
        self.chargeState = ""
        self.electricRange = 0
        self.totalRange = 0
        self.totalMiles = 0
        self.electricMiles = 0
        self.gasRange = 0
        self.gasFuelLevelPercentage = 0
        self.gasMiles = 0
        self.voltage = 0
        self.estimatedFullChargeBy = ""

    @property
    def name(self):
        return "{0} {1} {2}".format(self.year, self.make, self.model)

    @property
    def charging(self):
        return self.chargeState == "charging"

    def update(self, *args, **kwargs):
        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                raise KeyError("No attribute named %s" % k)

    def from_json(self, data):
        try:
            res = json.loads(data.decode("utf-8"))

            # I've never actually seen serverErrorMsgs, but allow for them
            if res["serverErrorMsgs"] or type(res["data"]) == str:
                raise ServerError(res)

            d = res["data"]

            self.plugged_in = d["plugState"] == "plugged"
            _LOGGER.debug("Data: {}".format(d))
            for a in CAR_ATTRS:
                # if the attr exists, set it
                if a in d:
                    setattr(self, a, d[a])

        except json.JSONDecodeError:
            _LOGGER.exception("Failure to decode json: %s" % data)
        except KeyError:
            _LOGGER.exception("Expected key not found")

    def __str__(self):
        return (
            "<EVCar name=%s, electricRange=%s miles, batteryLevel=%s%%, "
            "gasRange=%s miles, fuelEconomy=%s mpg, gasFuelLevelPercentage=%s%%, "
            "plugged_in=%s, "
            "totalMiles=%s miles, chargeState=%s, chargeMode=%s, "
            "estimatedFullChargeBy=%s>"
            % (
                self.name,
                self.electricRange,
                self.batteryLevel,
                self.gasRange,
                self.fuelEconomy,
                self.gasFuelLevelPercentage,
                self.plugged_in,
                self.totalMiles,
                self.chargeState,
                self.chargeMode,
                self.estimatedFullChargeBy,
            )
        )


class MyChevy(object):
    def __init__(self, user, passwd, country="us"):
        super(MyChevy, self).__init__()

        self.user = user
        self.passwd = passwd
        self.cars = []
        self.cookies = None
        self.history = []
        self.session = None
        self.account = None
        self.country = country

    def login(self):
        """New login path, to be used with json data path."""
        # Get the main page
        self.session = requests.Session()

        # It doesn't like an empty session so load the login page first.
        r = self.session.get(get_url("home", self.country), timeout=TIMEOUT)
        initial_url = urllib.parse.urlparse(r.request.url)
        nonce = urllib.parse.parse_qs(initial_url.query).get("nonce")[0]

        _LOGGER.debug("Initial URL %s, Nonce %s", initial_url, nonce)
        m = settings_json_re.search(r.text)
        if not m:
            raise ValueError("SETTINGS not found in response")

        settings_json = json.loads(m.group(1))
        csrf = settings_json["csrf"]
        trans_id = settings_json["transId"]

        _LOGGER.debug(
            "Settings %s, CSRF %s, Trans_id %s", settings_json, csrf, trans_id
        )

        # Login Request
        r = self.session.post(
            LOGIN_URL.format(trans_id),
            {
                "request_type": "RESPONSE",
                "logonIdentifier": self.user,
                "password": self.passwd,
            },
            headers={
                "X-CSRF-TOKEN": csrf,
            },
        )

        # Generate Auth Code and ID Token
        r = self.session.get(TOKEN_URL.format(csrf, trans_id))
        r.raise_for_status()
        _LOGGER.debug("ID Token Content: %s", r.content)
        m = id_token_re.search(r.text)
        if not m:
            raise ValueError("id_token not found in response")

        id_token = m.group(1)

        # Post ID Token
        r = self.session.post(
            get_url("oc_login", self.country),
            {"id_token": id_token},
        )
        r.raise_for_status()
        self.account = self.session.get(
            get_url("loginSuccessData", self.country), timeout=TIMEOUT
        )

    def get_cars(self):
        try:
            data = json.loads(self.account.content.decode("utf-8"))
            if data["serverErrorMsgs"]:
                raise Exception(data["serverErrorMsgs"])

            self.cars = []
            _LOGGER.debug("Vehicles: %s", data["data"]["vehicleMap"])
            for vid, vehicle in data["data"]["vehicleMap"].items():
                self.cars.append(EVCar(vehicle))
        except Exception:
            raise Exception(
                """
Something went wrong!

Cookies: %s

Content: %s

Location: %s
            """
                % (self.account.cookies, self.account.content, self.account.history)
            )

    @retry(ServerError, logger=_LOGGER)
    def _fetch_car(self, car):
        headers = {"user-agent": USER_AGENT}
        _LOGGER.debug("Fetching car...")
        now = int(round(time.time() * 1000))
        session = get_url("session", self.country).format(car.vin, car.onstar, now, KEY)
        res = self.session.get(
            session,
            headers=headers,
            cookies=self.cookies,
            allow_redirects=False,
            timeout=TIMEOUT,
        )

        now = int(round(time.time() * 1000))
        url = get_url("evstats", self.country).format(car.vin, car.onstar, now, KEY)
        res = self.session.get(
            url,
            headers=headers,
            cookies=self.cookies,
            allow_redirects=False,
            timeout=TIMEOUT,
        )

        _LOGGER.debug("Vehicle data: %s" % res.content)
        car.from_json(res.content)

    def update_cars(self):
        for c in self.cars:
            self._fetch_car(c)
        return self.cars
