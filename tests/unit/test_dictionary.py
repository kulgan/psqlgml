from unittest import mock

import pytest

from psqlgml import dictionary
from tests import helpers

pytestmark = [pytest.mark.dictionary]
REMOTE_GIT_URL = "https://github.com/NCI-GDC/gdcdictionary.git"
META = {
    "id": "test",
    "name": {"name": {"type": "string", "default": "Smokes"}},
    "age": {"age": {"type": "number", "default": 2}},
    "properties": {"$ref": ["#/name", "#/age"]},
}
DUMMY_SCHEMA = {"$ref": "_meta.yaml#/properties"}


def test_schema_resolution(local_dictionary: dictionary.Dictionary) -> None:
    assert local_dictionary.schema


@mock.patch.dict(dictionary.RESOLVERS, {"_meta.yaml": dictionary.Resolver("_meta.yaml", META)})
def test_resolvers():
    resolved = dictionary.resolve_schema(DUMMY_SCHEMA)
    assert "name" in resolved
    assert "age" in resolved


def test_dictionary(local_dictionary) -> None:
    assert {"programs", "projects", "cases"} == local_dictionary.links
    assert len(local_dictionary.all_associations()) == 4


def test_association__instance() -> None:
    a1 = dictionary.Association("src", "dst", "member_of", "link1")
    a2 = dictionary.Association("src", "dst", "member_of", "link1")
    a3 = dictionary.Association("src", "dst", "member_of", "link2")
    a4 = dictionary.Association("src", "dst", "member_of", "link2", is_reference=True)

    assert a1 == a2
    assert a1 != a3
    assert a3 != a4


def test_from_objects() -> None:

    d = dictionary.from_object(helpers.MiniDictionary.schema, name="mini", version="1.0.0")
    assert {"cases", "projects", "portions", "samples", "centers", "programs"} == d.links
    assert len(d.schema) == 6
