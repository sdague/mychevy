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
