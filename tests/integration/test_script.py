import json
from pathlib import Path

import pytest
import yaml
from pkg_resources import get_distribution

import psqlgml
from psqlgml import cli

VERSION = get_distribution(psqlgml.__name__).version


def test_version(cli_runner):
    result = cli_runner.invoke(cli.main, ["--version"])
    assert result.exit_code == 0
    assert f"version {VERSION}" in result.output


@pytest.mark.parametrize("dictionary", ["GDC", "GPAS"])
def test_generate_schema(cli_runner, dictionary, tmpdir):
    result = cli_runner.invoke(cli.main, ["generate", "-d", dictionary, "-o", tmpdir])
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
    result = cli_runner.invoke(cli.main, ["generate", "-d", dictionary, "-o", tmpdir])
    assert result.exit_code != 0

    json_path = Path(f"{tmpdir}/{dictionary.lower()}.json")
    yaml_path = Path(f"{tmpdir}/{dictionary.lower()}.yaml")

    assert json_path.exists() is False and yaml_path.exists() is False
