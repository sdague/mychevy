#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `mychevy` package."""

import unittest

import pytest

from mychevy.mychevy import EVCar, ServerError

CAR1 = {
    "vin": "fakevin",
    "vehicle_id": "123",
    "onstarAccountNumber": "123",
    "year": "2017",
    "make": "Chevy",
    "model": "Bolt",
    "imageUrl": ""
}

# DATA packet:
PKT1 = b'{"messages":[],"serverErrorMsgs":[],"data":{"dataAsOfDate":1516671611000,"batteryLevel":70,"chargeState":"not_charging","plugState":"plugged","rateType":"PEAK","voltage":240,"electricRange":132,"totalRange":132,"chargeMode":"DEPARTURE_BASED","electricMiles":1601,"gasMiles":0,"totalMiles":1601,"percentageOnElectric":1,"fuelEconomy":1000,"electricEconomy":45,"combinedEconomy":11,"fuelUsed":132,"electricityUsed":132,"estimatedGallonsFuelSaved":61.13,"estimatedCO2Avoided":1185.92,"estimatedFullChargeBy":"5:00 a.m."}}'  # noqa


class TestMyChevy(unittest.TestCase):

    def test_car_parse(self):
        car = EVCar(CAR1)
        assert car.vid == "123"

    def test_car_server_error(self):
        car = EVCar(CAR1)
        with pytest.raises(ServerError):
            car.from_json(
                '{"messages": [], "serverErrorMsgs": [], '
                '"data": "SERVER ERROR"}')

    def test_json_parse(self):
        car = EVCar(CAR1)
        car.from_json(PKT1)

        assert car.plugged_in is True
        assert car.batteryLevel == 70
        assert car.voltage == 240
        assert car.totalRange == 132
        assert car.totalMiles == 1601
        assert car.estimatedFullChargeBy == "5:00 a.m."
