import json
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner
from pkg_resources import get_distribution

import psqlgml
from psqlgml import cli
from psqlgml.typings import DictionaryType

VERSION = get_distribution(psqlgml.__name__).version


def test_version(cli_runner):
    result = cli_runner.invoke(cli.app, ["--version"])
    assert result.exit_code == 0
    assert f"version {VERSION}" in result.output


@pytest.mark.parametrize("dictionary", ["GDC", "GPAS"])
def test_generate_schema(cli_runner, dictionary, tmpdir):
    result = cli_runner.invoke(cli.app, ["generate", "-d", dictionary, "-o", tmpdir])
    assert result.exit_code == 0
    json_path = Path(f"{tmpdir}/{dictionary.lower()}.json")
    yaml_path = Path(f"{tmpdir}/{dictionary.lower()}.yaml")

    assert json_path.exists() and yaml_path.exists()

    # check if they are loadable
    with json_path.open("r") as f:
        jso = json.load(f)
        assert "properties" in jso

    with yaml_path.open("r") as y:
        ymo = yaml.safe_load(y)
        assert "properties" in ymo


@pytest.mark.parametrize("dictionary", ["GDCX", "GPAX"])
def test_generate_schema_unknown_dictionary(cli_runner, dictionary, tmpdir):
    result = cli_runner.invoke(cli.app, ["generate", "-d", dictionary, "-o", tmpdir])
    assert result.exit_code != 0

    json_path = Path(f"{tmpdir}/{dictionary.lower()}.json")
    yaml_path = Path(f"{tmpdir}/{dictionary.lower()}.yaml")

    assert json_path.exists() is False and yaml_path.exists() is False


@pytest.mark.parametrize(
    "dictionary, data_file",
    [
        ("GDC", "simple_valid.yaml"),
        ("GPAS", "simple_valid.json"),
    ],
)
def test_validate_file(
    cli_runner: CliRunner, dictionary: DictionaryType, tmpdir: str, data_dir: str, data_file: str
):
    result = cli_runner.invoke(
        cli.app,
        [
            "validate",
            "-d",
            dictionary,
            "--data-dir",
            data_dir,
            "-v",
            "ALL",
            "-f",
            data_file,
        ],
    )
    print(result.output)
    assert result.exit_code == 0
