import logging
import sys
from dataclasses import dataclass
from logging.config import dictConfig
from typing import Literal

import click
import yaml
from pkg_resources import get_distribution, resource_filename

import psqlgml

VERSION = get_distribution(psqlgml.__name__).version
logger: logging.Logger


@dataclass(frozen=True)
class LoggingConfig:
    level: str


@click.group()
@click.version_option(VERSION)
def main():
    """psqlgml script for generating, validating and viewing graph data"""
    global logger

    configure_logger(LoggingConfig(level="DEBUG"))
    logger = logging.getLogger("oshoo")


@click.command(name="generate")
@click.option(
    "-d",
    "--dictionary",
    type=click.Choice(["GDC", "GPAS"], case_sensitive=False),
    default="GPAS",
    help="Dictionary to generate schema for",
)
@click.option(
    "-o",
    "--output-dir",
    type=click.Path(exists=True),
    required=False,
    help="Output directory to store generated schema",
)
def generate_schema(dictionary: Literal["GPAS", "GDC"], output_dir: str):
    """Generate schema based on currently installed dictionaries"""
    logging.debug(f"Generating psqlgml schema for {dictionary} Dictionary")

    from psqlgml.core import generate_schema

    output_dir = output_dir or resource_filename(psqlgml.__name__, "schema")
    schema_file = generate_schema(output_dir, dictionary)
    logging.info(f"schema generation completed successfully: {schema_file}")


@click.command(name="validate")
@click.option(
    "-d",
    "--dictionary",
    type=click.Choice(["GDC", "GPAS"], case_sensitive=False),
    default="GPAS",
    help="Dictionary to generate schema for",
)
@click.option(
    "-v",
    "--validator",
    type=click.Choice(["DATA", "SCHEMA"], case_sensitive=False),
    required=False,
    help="Dictionary schema to use for validation",
)
@click.option("--data-dir", type=click.Path(exists=True))
@click.option(
    "-f", "--data-file", type=click.Path(exists=True), required=True, help="The file to validate"
)
def validate_file(data_file: click.Path, dictionary: str, data_dir: str, validator: str):
    from psqlgml.core import validate

    validate(data_file, dictionary, validator)


def configure_logger(cfg: LoggingConfig):
    lcfg = yaml.safe_load(
        f"""
        version: 1
        formatters:
          simple:
            format: '%(asctime)s %(levelname)s [%(name)s:%(lineno)d] %(message)s'
        handlers:
          console:
            class: logging.StreamHandler
            level: {cfg.level}
            formatter: simple
            stream: ext://sys.stdout
        loggers:
          psqlgml:
            level: {cfg.level}
            handlers:
              - console
            propagate: no
          root:
            level: {cfg.level}
            handlers:
              - console
    """
    )

    dictConfig(lcfg)


main.add_command(generate_schema)


if __name__ == "__main__":
    main(sys.argv[1:])
