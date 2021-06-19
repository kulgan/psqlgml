import click

from psqlml import tick


@click.group()
def main():
    pass


@click.command(name="generate")
@click.option()
def generate():
    pass
