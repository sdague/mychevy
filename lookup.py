#!/usr/bin/env python3

import asyncio

from mychevy.mychevy import MyChevy

import configparser

async def print_data():
    config = configparser.ConfigParser()
    config.read("config.ini")

    page = MyChevy(config["default"]["user"], config["default"]["passwd"])

    data = await page.data()
    print(data)

def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(print_data())


main()
