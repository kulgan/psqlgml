import pytest
from click.testing import CliRunner

from psqlgml import dictionary


@pytest.fixture(scope="session")
def cli_runner():
    return CliRunner()


@pytest.fixture(scope="session")
def remote_dictionary() -> dictionary.Dictionary:
    return dictionary.load(version="2.3.0")
