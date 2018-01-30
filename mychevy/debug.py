# -*- coding: utf-8 -*-

"""Console script for mychevy."""

import configparser

import click

from mychevy.mychevy import MyChevy

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.command(context_settings=CONTEXT_SETTINGS)
@click.option('--config', '-c', type=click.File('r'),
              required=True,
              help="Config file with my.chevy credentials")
def main(config=None, show_browser=None):
    """Console script for mychevy"""
    cfile = configparser.ConfigParser()
    cfile.read_file(config)

    page = MyChevy(cfile["default"]["user"], cfile["default"]["passwd"])
    click.echo("Logging in... this takes a bit")
    page.login()
    page.get_cars()
    click.echo("Displaying found cars")
    for c in page.cars:
        click.echo(c)
    page.car_data()


if __name__ == "__main__":
    main()
