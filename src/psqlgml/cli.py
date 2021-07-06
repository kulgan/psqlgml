import logging
import sys
from logging.config import dictConfig
from typing import Optional

import attr
import click
import yaml
from pkg_resources import get_distribution, resource_filename

import psqlgml
from psqlgml.typings import DictionaryType, Literal, ValidatorType

VERSION = get_distribution(psqlgml.__name__).version
logger: logging.Logger


@attr.s(frozen=True, auto_attribs=True)
class LoggingConfig:
    level: str


@click.group()
@click.version_option(VERSION)
def main() -> None:
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
def schema_gen(dictionary: DictionaryType, output_dir: str) -> None:
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
    type=click.Choice(["ALL", "DATA", "SCHEMA"], case_sensitive=False),
    required=False,
    default="ALL",
    help="Dictionary schema to use for validation",
)
@click.option("--data-dir", type=click.Path(exists=True))
@click.option(
    "-f", "--data-file", type=click.Path(exists=True), required=True, help="The file to validate"
)
def validate_file(
    data_file: str,
    dictionary: DictionaryType,
    data_dir: str,
    validator: ValidatorType,
) -> None:
    from psqlgml.core import validate

    validate(data_dir=data_dir, data_file=data_file, dictionary=dictionary, validator=validator)


@click.command(name="visualize")
@click.option(
    "-o",
    "--output-dir",
    type=click.Path(exists=True),
    required=False,
    default="/tmp",
    help="Output directory to store generated image file",
)
@click.option(
    "--data-dir", type=click.Path(exists=True), help="Base directory to look up data files"
)
@click.option("-f", "--data-file", type=str, required=True, help="The file to visualize")
def visualize_data(output_dir: str, data_dir: str, data_file: str) -> None:
    from psqlgml import visualize

    visualize.visualize_graph(data_dir, data_file, output_dir)


def configure_logger(cfg: LoggingConfig) -> None:
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


main.add_command(schema_gen)
main.add_command(visualize_data)
main.add_command(validate_file)

if __name__ == "__main__":
    main(sys.argv[1:])
