from typing import Dict

from psqlgml import resources as r
from psqlgml.types import GmlData

JSON_PAYLOAD = "simple_valid.json"


def test_merge_resource(data_dir):

    merged = r.load_resource(data_dir, JSON_PAYLOAD)
    assert "extends" not in merged

    nodes = merged["nodes"]
    assert len(nodes) == 5

    edges = merged["edges"]
    assert len(edges) == 3


def test_load_all(data_dir):
    payloads: Dict[str, GmlData] = r.load_by_resource(data_dir, JSON_PAYLOAD)
    assert len(payloads) == 2
    sources = [JSON_PAYLOAD, "simple_valid.yaml"]
    for source in sources:
        payload = payloads[source]
        assert "nodes" in payload
