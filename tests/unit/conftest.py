import pkg_resources
import pytest


@pytest.fixture()
def data_dir():
    return pkg_resources.resource_filename("tests", "data")
