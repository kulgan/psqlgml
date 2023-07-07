import logging
import sys
from logging.config import dictConfig
from typing import List

import attr
import click
import yaml

import psqlgml

__all__: List[str] = []

logger: logging.Logger


@attr.s(frozen=True, auto_attribs=True)
class LoggingConfig:
    level: str


@click.group()
@click.version_option(psqlgml.VERSION)
def app() -> None:
    """psqlgml script for generating, validating and viewing graph data"""
    global logger

    configure_logger(LoggingConfig(level="ERROR"))
    logger = logging.getLogger(__name__)


@click.option(
    "-d",
    "--dictionary",
    type=str,
    default="https://github.com/NCI-GDC/gdcdictionary.git",
    help="Remote git dictionary repository url",
)
@click.option(
    "-v",
    "--version",
    type=str,
    required=True,
    default="master",
    help="git tag, branch or commit for the selected dictionary",
)
@click.option(
    "-n", "--name", type=str, default="gdcdictionary", help="label/name for the dictionary"
)
@click.option(
    "-p",
    "--schema-path",
    type=str,
    default="gdcdictionary/schemas",
    help="Relative path to schema directory",
)
@click.option(
    "-o",
    "--output-dir",
    type=click.Path(exists=True),
    required=False,
    help="Output directory to store generated schema",
)
@click.option(
    "-f",
    "--force/--no-force",
    type=bool,
    default=False,
    is_flag=True,
    help="Force regeneration if already exists",
)
@click.option(
    "-t",
    "--tag/--no-tag",
    type=bool,
    default=True,
    is_flag=True,
    help="True if specified version is a tag, defaults to True",
)
@app.command(name="generate")
def schema_gen(
    dictionary: str,
    output_dir: str,
    version: str,
    name: str,
    schema_path: str,
    force: bool,
    tag: bool,
) -> None:
    """Generate schema for specified dictionary"""
    global logger
    logger.debug(f"Generating psqlgml schema for {dictionary} Dictionary")

    current_dictionary = (
        psqlgml.DictionaryReader(name, version)
        .git(url=dictionary, schema_path=schema_path, overwrite=force, is_tag=tag)
        .read()
    )
    schema_file = psqlgml.generate(
        loaded_dictionary=current_dictionary,
        output_location=output_dir,
    )
    logging.info(f"schema generation completed successfully: {schema_file}")


@click.option(
    "-d",
    "--dictionary",
    type=str,
    default="gdcdictionary",
    help="Dictionary name/label to use for validation",
)
@click.option(
    "-v",
    "--version",
    type=str,
    required=True,
    default="master",
    help="dictionary schema version, which is either a git hash, branch or tag. "
    "Should match a previously generated schema",
)
@click.option(
    "-V",
    "--validator",
    type=click.Choice(["ALL", "DATA", "SCHEMA"], case_sensitive=False),
    required=False,
    default="ALL",
    help="Dictionary schema to use for validation",
)
@click.option("--data-dir", type=click.Path(exists=True))
@click.option("-f", "--data-file", type=str, required=True, help="The file to validate")
@app.command(name="validate", help="Perform validation on resource files")
def validate_file(
    version: str,
    data_file: str,
    dictionary: str,
    data_dir: str,
    validator: psqlgml.ValidatorType,
) -> None:
    global logger
    logger.debug(f"running {validator} validators for {data_dir}/{data_file}")

    gml_schema = psqlgml.read_schema(dictionary, version)
    loaded = psqlgml.load(name=dictionary, version=version)
    request = psqlgml.ValidationRequest(
        data_file=data_file, data_dir=data_dir, schema=gml_schema, dictionary=loaded
    )
    psqlgml.validate(
        request=request,
        validator=validator,
        print_error=True,
    )


@click.option(
    "-o",
    "--output-dir",
    type=click.Path(exists=True),
    required=False,
    default="/tmp",
    help="Output directory to store generated image file",
)
@click.option(
    "--output-format",
    type=click.Choice(["jpeg", "pdf", "png"]),
    required=False,
    default="png",
    help="Generated image formal",
)
@click.option(
    "-d", "--data-dir", type=click.Path(exists=True), help="Base directory to look up data files"
)
@click.option("-f", "--data-file", type=str, required=True, help="The file to visualize")
@click.option("-s", "--show/--no-show", is_flag=True, default=True)
@app.command(name="visualize", help="Visualize a resource file using graphviz")
def visualize_data(
    output_dir: str,
    data_dir: str,
    data_file: str,
    output_format: psqlgml.RenderFormat,
    show: bool,
) -> None:
    psqlgml.draw(data_dir, data_file, output_dir, output_format, show_rendered=show)


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


if __name__ == "__main__":
    app(sys.argv[1:])
