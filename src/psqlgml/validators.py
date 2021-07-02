import json
from typing import Dict, List, Set

import pkg_resources
from jsonschema import Draft7Validator

from psqlgml.models import (
    Association,
    DictionaryType,
    GdcSchema,
    Link,
    SchemaData,
    SchemaType,
    SchemaViolation,
    UniqueFieldType,
)
from psqlgml.resources import load_all
from psqlgml.typings import Literal, Protocol

SCHEMA: Dict[DictionaryType, Draft7Validator] = {}


class Validator(Protocol):
    def __call__(
        self, payload: Dict[str, SchemaData], schema_type: DictionaryType = "GDC"
    ) -> Dict[str, Set[SchemaViolation]]:
        ...


def duplicate_definition_validator(
    payload: Dict[str, SchemaData], schema_type: DictionaryType = "GDC"
) -> Dict[str, Set[SchemaViolation]]:
    """Raises a violation if a given unique_id is re-used while redefining another node"""

    uids: Set[str] = set()

    violations: Dict[str, Set[SchemaViolation]] = {}
    for resource, schema_data in payload.items():
        nodes = schema_data["nodes"]
        unique_field: UniqueFieldType = schema_data.get("unique_field", "submitter_id")

        sub_violations: Set[SchemaViolation] = set()
        for index, node in enumerate(nodes):
            uid = node[unique_field]

            if uid in uids:
                sub_violations.add(
                    SchemaViolation(
                        path=f"nodes.{index}",
                        schema_type=schema_type,
                        message=f"{unique_field} redefined for {uid}",
                    )
                )
        if sub_violations:
            violations[resource] = sub_violations
    return violations


def undefined_link_validator(
    payload: Dict[str, SchemaData], schema_type: DictionaryType = "GDC"
) -> Dict[str, Set[SchemaViolation]]:

    violations: Dict[str, Set[SchemaViolation]] = {}
    for resource, schema_data in payload.items():
        unique_field: UniqueFieldType = schema_data.get("unique_field", "submitter_id")
        edges = schema_data["edges"]
        nodes = schema_data["nodes"]
        entries: Set[str] = {n[unique_field] for n in nodes}

        sub_violations: Set[SchemaViolation] = set()
        for index, edge in enumerate(edges):
            for key in ["src", "dst"]:  # type: Literal["src", "dst"]
                if edge[key] in entries:
                    continue

                sub_violations.add(
                    SchemaViolation(
                        path=f"edges.{index}",
                        schema_type=schema_type,
                        message=f"node with {unique_field} value {edge[key]} not defined",
                    )
                )
        if sub_violations:
            violations[resource] = sub_violations
    return violations


def association_validator(
    payload: Dict[str, SchemaData], schema_type: DictionaryType = "GDC"
) -> Dict[str, Set[SchemaViolation]]:

    violations: Dict[str, Set[SchemaViolation]] = {}
    node_types: Dict[str, str] = {}
    json_schema = SchemaType.from_value(schema_type)
    for resource, schema in payload.items():
        unique_field: UniqueFieldType = schema.get("unique_field", "submitter_id")
        for node in schema["nodes"]:
            unique_id = node[unique_field]
            node_types[unique_id] = node["label"]

    sub_violations: Set[SchemaViolation] = set()
    for resource, schema in payload.items():

        for index, edge in enumerate(schema["edges"]):
            src = edge["src"]
            dst = edge["dst"]
            edge_label = edge.get("label")
            src_label = node_types[src]
            dst_label = node_types[dst]

            associations = json_schema.associations(src_label)
            filtered = [assoc for assoc in associations if assoc.dst == dst_label]
            if not filtered:
                sub_violations.add(
                    SchemaViolation(
                        path=f"edges.{index}",
                        schema_type=schema_type,
                        message=f"node type {src_label} cannot be linked to {dst_label} ",
                    )
                )
            # validate edge label
            if edge_label and not [assoc for assoc in filtered if assoc.label == edge_label]:
                sub_violations.add(
                    SchemaViolation(
                        path=f"edges.{index}",
                        schema_type=schema_type,
                        violation_type="warning",
                        message=f"Invalid edge name {edge_label} for edge {src_label} -> {dst_label} ",
                    )
                )
        if sub_violations:
            violations[resource] = sub_violations

    return violations


class ValidatorFactory:
    def __init__(self, resource_dir: str, register_defaults: bool = False):

        self.resource_dir = resource_dir
        self.validators: List[Validator] = []

        if register_defaults:
            self.__register_defaults()

    def register_validator(self, validator: Validator):
        self.validators.append(validator)

    def __register_defaults(self):
        self.register_validator(schema_validator)
        self.register_validator(duplicate_definition_validator)
        self.register_validator(undefined_link_validator)
        self.register_validator(association_validator)

    def validate(
        self, resource_name: str, resource_type: DictionaryType = "GPAS"
    ) -> Dict[str, Set[SchemaViolation]]:
        payload = load_all(self.resource_dir, resource_name)

        violations: Dict[str, Set[SchemaViolation]] = {}

        for validator in self.validators:
            sub_violations = validator(payload, resource_type)

            for resource, sub_violation in sub_violations.items():
                if resource in violations:
                    violations[resource].update(sub_violation)
                else:
                    violations[resource] = sub_violation
            print(f"violations {validator} - {sub_violations}")
        return violations


def validate_schema(
    obj: SchemaData, schema_type: DictionaryType = "GPAS"
) -> Set[SchemaViolation]:
    ver = f"schema/{schema_type.lower()}.json"

    if schema_type not in SCHEMA:
        with pkg_resources.resource_stream(__name__, ver) as stream:
            schema = json.load(stream)
        SCHEMA[schema_type] = Draft7Validator(schema=schema)

    vs = SCHEMA[schema_type]
    violations: Set[SchemaViolation] = set()
    for e in vs.iter_errors(obj):
        str_path = ".".join([str(entry) for entry in e.path])
        violations.add(SchemaViolation(path=str_path, schema_type=schema_type, message=e.message))
    return violations


def schema_validator(
    obj: Dict[str, SchemaData], schema_type: DictionaryType = "GPAS"
) -> Dict[str, Set[SchemaViolation]]:
    violations: Dict[str, Set[SchemaViolation]] = {}

    for resource, schema_data in obj.items():
        schema_violations = validate_schema(schema_data, schema_type)
        violations[resource] = schema_violations
    return violations


VALIDATORS: Dict[str, List[Validator]] = {
    "SCHEMA": [schema_validator],
    "DATA": [association_validator, undefined_link_validator, duplicate_definition_validator],
}
