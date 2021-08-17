from unittest import mock

from psqlgml import dictionary

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


def test_association__instance():
    a1 = dictionary.Association("src", "dst", "link1")
    a2 = dictionary.Association("src", "dst", "link1")
    a3 = dictionary.Association("src", "dst", "link2")

    assert a1 == a2
    assert a1 != a3
