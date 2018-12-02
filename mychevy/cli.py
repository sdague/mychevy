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
@click.option('--show-browser', '-S', is_flag=True,
              help="Show browser window when running")
def main(config=None, show_browser=None):
    """Console script for mychevy"""
    cfile = configparser.ConfigParser()
    cfile.read_file(config)

    page = MyChevy(cfile["default"]["user"], cfile["default"]["passwd"])
    click.echo("Loading data, this takes up to 2 minutes...")
    page.login()
    page.get_cars()
    cars = page.update_cars()
    for c in cars:
        click.echo(c)


if __name__ == "__main__":
    main()
