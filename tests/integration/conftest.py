import pytest
from click.testing import CliRunner

import psqlgml


@pytest.fixture(scope="session")
def cli_runner():
    return CliRunner()


@pytest.fixture(scope="session")
def remote_dictionary() -> psqlgml.Dictionary:
    return psqlgml.load(version="2.3.0")
