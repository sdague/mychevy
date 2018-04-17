# -*- coding: utf-8 -*-

"""Console script for mychevy."""

import configparser
import logging

import click

from mychevy.mychevy import MyChevy, ServerError

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.command(context_settings=CONTEXT_SETTINGS)
@click.option('--config', '-c', type=click.File('r'),
              required=True,
              help="Config file with my.chevy credentials")
@click.option('--verbose', '-v', default=False, is_flag=True,
              help="Run more verbose")
def main(config=None, verbose=False):
    """Console script for mychevy"""
    cfile = configparser.ConfigParser()
    cfile.read_file(config)

    if verbose:
        logging.basicConfig(level=logging.DEBUG)

    page = MyChevy(cfile["default"]["user"], cfile["default"]["passwd"])
    click.echo("Logging in... this takes a bit")
    page.login()
    page.get_cars()
    click.echo("Displaying found cars")
    for c in page.cars:
        click.echo(c)
    click.echo("Updating cars with data")
    try:
        if cfile.has_option("default","vin"):
            page.update_cars(cfile["default"]["vin"])
        else:
            page.update_cars()

        click.echo("Displaying found cars with data")
        for c in page.cars:
            click.echo(c)
    except ServerError as e:
        click.echo("OnStar Network Failure: %s" % e)


if __name__ == "__main__":
    main()
