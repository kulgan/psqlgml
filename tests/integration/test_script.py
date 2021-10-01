import json
import os
from pathlib import Path
from unittest import mock

import pytest
import yaml
from click.testing import CliRunner
from PIL import Image
from pkg_resources import get_distribution

import psqlgml
from psqlgml import cli
from tests.helpers import SchemaInfo

pytestmark = [pytest.mark.slow, pytest.mark.dictionary]
VERSION = get_distribution(psqlgml.__name__).version
REMOTE_GIT_URL = "https://github.com/NCI-GDC/gdcdictionary.git"


def test_version(cli_runner: CliRunner) -> None:
    result = cli_runner.invoke(cli.app, ["--version"])
    assert result.exit_code == 0
    assert f"version {VERSION}" in result.output


@pytest.mark.parametrize("version", ["2.3.0", "2.4.0"])
def test_schema_generate(cli_runner: CliRunner, version: str, tmpdir: Path) -> None:
    dictionary = "gdcdictionary"
    result = cli_runner.invoke(cli.app, ["generate", "-v", version, "-o", tmpdir, "-f"])
    assert result.exit_code == 0
    json_path = Path(f"{tmpdir}/{dictionary}/{version}/schema.json")
    yaml_path = Path(f"{tmpdir}/{dictionary}/{version}/schema.yaml")

    assert json_path.exists() and yaml_path.exists()

    # check if they are loadable
    with json_path.open("r") as f:
        jso = json.load(f)
        assert "properties" in jso
        assert jso["url"] == REMOTE_GIT_URL
        assert jso["version"] == version

    with yaml_path.open("r") as y:
        ymo = yaml.safe_load(y)
        assert "properties" in ymo
        assert jso["url"] == REMOTE_GIT_URL
        assert jso["version"] == version


def test_schema_generate_local(cli_runner: CliRunner, data_dir: str, tmpdir: Path) -> None:

    name = "dictionary"

    with mock.patch.dict(os.environ, {"GML_DICTIONARY_HOME": data_dir}):
        result = cli_runner.invoke(
            cli.app,
            ["generate", "-n", name, "-v", "0.1.0", "-o", tmpdir],
        )
        assert result.exit_code == 0

        json_path = Path(f"{tmpdir}/{name}/0.1.0/schema.json")
        yaml_path = Path(f"{tmpdir}/{name}/0.1.0/schema.yaml")

        assert json_path.exists() and yaml_path.exists()


@pytest.mark.parametrize("render_format", ["png", "jpeg", "pdf"])
@pytest.mark.parametrize("data_file", ["simple_valid.json", "simple_valid.yaml"])
def test_visualize_data(
    cli_runner: CliRunner,
    data_dir: str,
    tmpdir: Path,
    render_format: psqlgml.types.RenderFormat,
    data_file: str,
) -> None:
    result = cli_runner.invoke(
        cli.app,
        [
            "visualize",
            "-f",
            data_file,
            "-o",
            tmpdir,
            "--output-format",
            render_format,
            "-d",
            data_dir,
            "--no-show",
        ],
    )
    assert result.exit_code == 0

    dot_output = Path(f"{tmpdir}/simple_valid.gv.{render_format}")
    assert dot_output.exists()

    if render_format == "pdf":
        return

    img = Image.open(dot_output)
    assert img.format.lower() == render_format


@pytest.mark.parametrize(
    "dictionary, data_file, version",
    [
        ("dictionary", "simple_valid.yaml", "0.1.0"),
        ("dictionary", "simple_valid.json", "0.1.0"),
    ],
)
def test_validate_file(
    cli_runner: CliRunner,
    data_dir: str,
    local_schema: SchemaInfo,
    dictionary: str,
    data_file: str,
    version: str,
):
    with mock.patch.dict(
        os.environ, {"GML_SCHEMA_HOME": local_schema.source_dir, "GML_DICTIONARY_HOME": data_dir}
    ):
        result = cli_runner.invoke(
            cli.app,
            [
                "validate",
                "-d",
                dictionary,
                "--data-dir",
                data_dir,
                "-V",
                "ALL",
                "-v",
                version,
                "-f",
                data_file,
            ],
        )
        print(result.output)
        assert result.exit_code == 0
