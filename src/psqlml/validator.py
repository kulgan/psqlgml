"""JSON schema and entry data validations"""

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Literal

import pkg_resources
import yaml
from jsonschema import Draft7Validator

from psqlml.models import UNIQUE_FIELD_TYPE, Edge, Schema


@dataclass
class SchemaViolation:
    path: str
    message: str
    violation_type: Literal["error", "warning"] = "error"


def validate(obj: Dict, model: str, version: str = "0.1.0") -> List[SchemaViolation]:
    ver = f"schema/{version}/{model.lower()}.json"
    with pkg_resources.resource_stream(__name__, ver) as stream:
        schema = json.load(stream)

    violations: List[SchemaViolation] = []
    vs = Draft7Validator(schema=schema)
    for e in vs.iter_errors(obj):
        str_path = ".".join([str(entry) for entry in e.path])
        violations.append(SchemaViolation(path=str_path, message=e.message))
    return violations


def load_resource(location: str) -> Schema:
    extension = location.split(".")[-1]
    with open(location, "r") as r:
        if extension == "json":
            return json.loads(r.read())

        if extension in ["yml", "yaml"]:
            return yaml.safe_load(r)

        raise ValueError(f"Unsupported file type {extension}")


def validate_relations(rss: Schema) -> List[SchemaViolation]:
    violations: List[SchemaViolation] = []
    unique_field: UNIQUE_FIELD_TYPE = rss.get("unique_field", "submitter_id")

    nodes = rss["nodes"]
    edges: List[Edge] = rss["edges"]
    entries: Dict[str, Dict[str, Any]] = {}
    for index, node in enumerate(nodes):
        uid = node[unique_field]

        if uid in entries:
            violations.append(
                SchemaViolation(
                    path=f"nodes.{index}", message=f"{unique_field} redefined for {uid}"
                )
            )
            continue
        entries[uid] = node
    for index, edge in enumerate(edges):
        src = entries.get(edge["src"])
        if not src:
            violations.append(
                SchemaViolation(
                    path=f"edges.{index}",
                    message=f"node with {unique_field} value {edge['src']} not defined",
                )
            )
        dst = entries.get(edge["dst"])
        if not dst:
            violations.append(
                SchemaViolation(
                    path=f"edges.{index}",
                    message=f"node with {unique_field} value {edge['dst']} not defined",
                )
            )

    return violations


def is_valid(resource_location: str, schema_version: str = "0.1.0"):

    rss: Schema = load_resource(resource_location)
    violations: List[SchemaViolation] = validate(rss, model="GPAS", version=schema_version)
    violations += validate_relations(rss)
    print(violations)
    return not violations


if __name__ == "__main__":
    # sample = "/home/rogwara/git/graphmanager/tests/data/exports/gpas_sample.json"
    sample = "/home/rogwara/git/graphmanager/tests/data/exports/gpas_sanger.yaml"

    is_valid(sample)
