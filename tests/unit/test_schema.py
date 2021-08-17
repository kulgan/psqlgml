import json
from pathlib import Path

import pytest
import yaml

from psqlgml import dictionary, schema
from tests.helpers import SchemaInfo


def test_generate(local_dictionary: dictionary.Dictionary, tmpdir: Path) -> None:
    output_location = f"{tmpdir}"
    schema.generate(
        output_location=output_location,
        loaded_dictionary=local_dictionary,
    )

    json_path = Path(f"{tmpdir}/{local_dictionary.name}/{local_dictionary.version}/schema.json")
    yaml_path = Path(f"{tmpdir}/{local_dictionary.name}/{local_dictionary.version}/schema.yaml")

    assert json_path.exists() and yaml_path.exists()

    # check if they are loadable
    with json_path.open("r") as f:
        jso = json.load(f)
        assert "properties" in jso

    with yaml_path.open("r") as y:
        ymo = yaml.safe_load(y)
        assert "properties" in ymo


def test_read(local_schema: SchemaInfo):
    s = schema.read(
        version=local_schema.version,
        name=local_schema.name,
        schema_location=local_schema.source_dir,
    )
    assert s["version"] == local_schema.version
    assert s["definitions"]["program"]
    assert s["definitions"]["project"]


def test_read__invalid(local_schema: SchemaInfo):
    with pytest.raises(ValueError):
        schema.read(
            version=local_schema.version, name="smokes", schema_location=local_schema.source_dir
        )
