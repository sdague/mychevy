#!/usr/bin/env python3

from mychevy.mychevy import MyChevy

import configparser

def print_data():
    config = configparser.ConfigParser()
    config.read("config.ini")

    page = MyChevy(config["default"]["user"], config["default"]["passwd"],
                   headless=False)

    data = page.data()
    print(data)

def main():
    print_data()

main()
