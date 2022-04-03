from pathlib import Path

import pkg_resources
import pytest

import psqlgml
from tests.helpers import SchemaInfo


@pytest.fixture(scope="session")
def data_dir() -> str:
    return pkg_resources.resource_filename("tests", "data")


@pytest.fixture(scope="session")
def local_dictionary(data_dir: str) -> psqlgml.Dictionary:
    return psqlgml.load_local(version="0.1.0", name="dictionary", dictionary_location=data_dir)


@pytest.fixture()
def local_schema(local_dictionary: psqlgml.Dictionary, tmpdir: Path) -> SchemaInfo:
    psqlgml.generate(loaded_dictionary=local_dictionary, output_location=str(tmpdir))
    return SchemaInfo(
        version=local_dictionary.version, name=local_dictionary.name, source_dir=str(tmpdir)
    )


@pytest.fixture()
def test_schema(local_schema: SchemaInfo) -> psqlgml.GmlSchema:
    return psqlgml.read_schema(
        name=local_schema.name,
        version=local_schema.version,
        schema_location=local_schema.source_dir,
    )
