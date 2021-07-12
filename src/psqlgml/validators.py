import json
from typing import Dict, List, Set, cast

import attr
import pkg_resources
from jsonschema import Draft7Validator

from psqlgml.models import SchemaData, SchemaType
from psqlgml.resources import load_all
from psqlgml.typings import (
    DictionaryType,
    Literal,
    Protocol,
    UniqueFieldType,
    ValidatorType,
)

SCHEMA: Dict[DictionaryType, Draft7Validator] = {}
ViolationType = Literal[
    "Link Association Violation",
    "Duplicate Definition Violation",
    "Jsonschema Violation",
    "Undefined Link Violation",
]


@attr.s(frozen=True, auto_attribs=True)
class DataViolation:
    name: ViolationType
    path: str
    message: str
    schema_type: DictionaryType
    violation_type: Literal["error", "warning"] = "error"


class Validator(Protocol):
    def __call__(
        self, payload: Dict[str, SchemaData], schema_type: DictionaryType = "GDC"
    ) -> Dict[str, Set[DataViolation]]:
        ...


def duplicate_definition_validator(
    payload: Dict[str, SchemaData], schema_type: DictionaryType = "GDC"
) -> Dict[str, Set[DataViolation]]:
    """Raises a violation if a given unique_id is re-used while redefining another node"""

    uids: Set[str] = set()

    violations: Dict[str, Set[DataViolation]] = {}
    for resource, schema_data in payload.items():
        nodes = schema_data["nodes"]
        unique_field: UniqueFieldType = schema_data.get("unique_field", "submitter_id")

        sub_violations: Set[DataViolation] = set()
        for index, node in enumerate(nodes):
            uid = node[unique_field]

            if uid in uids:
                sub_violations.add(
                    DataViolation(
                        name="Duplicate Definition Violation",
                        path=f"nodes.{index}",
                        schema_type=schema_type,
                        message=f"{unique_field} redefined for {uid}",
                    )
                )
        violations[resource] = sub_violations
    return violations


def undefined_link_validator(
    payload: Dict[str, SchemaData], schema_type: DictionaryType = "GDC"
) -> Dict[str, Set[DataViolation]]:

    violations: Dict[str, Set[DataViolation]] = {}
    entries: Set[str] = set()
    for resource, schema_data in payload.items():
        unique_field: UniqueFieldType = schema_data.get("unique_field", "submitter_id")
        uids = (n[unique_field] for n in schema_data["nodes"])
        entries.update(uids)

    for resource, schema_data in payload.items():
        edges = schema_data["edges"]
        sub_violations: Set[DataViolation] = set()

        for index, edge in enumerate(edges):
            for key in ["src", "dst"]:
                key = cast(Literal["src", "dst"], key)
                if edge[key] in entries:
                    continue

                sub_violations.add(
                    DataViolation(
                        name="Undefined Link Violation",
                        path=f"edges.{index}",
                        schema_type=schema_type,
                        violation_type="warning",
                        message=f"node with unique key value {edge[key]} not defined",
                    )
                )
        violations[resource] = sub_violations
    return violations


def association_validator(
    payload: Dict[str, SchemaData], schema_type: DictionaryType = "GDC"
) -> Dict[str, Set[DataViolation]]:

    violations: Dict[str, Set[DataViolation]] = {}
    node_types: Dict[str, str] = {}
    json_schema = SchemaType.from_value(schema_type)
    for resource, schema in payload.items():
        unique_field: UniqueFieldType = schema.get("unique_field", "submitter_id")
        for node in schema["nodes"]:
            unique_id = node[unique_field]
            node_types[unique_id] = node["label"]

    for resource, schema in payload.items():

        sub_violations: Set[DataViolation] = set()
        for index, edge in enumerate(schema["edges"]):
            src = edge["src"]
            dst = edge["dst"]
            edge_label = edge.get("label")
            src_label = node_types[src]
            dst_label = node_types[dst]

            associations = json_schema.associations(src_label)
            filtered = [assoc for assoc in associations if assoc.dst == dst_label]
            if not filtered:
                print(f"{json_schema} - {src_label}, {dst_label}, {associations}")
                sub_violations.add(
                    DataViolation(
                        name="Link Association Violation",
                        path=f"edges.{index}",
                        schema_type=schema_type,
                        message=f"node type {src_label} cannot be linked to {dst_label} ",
                    )
                )
            # validate edge label
            if edge_label and not [assoc for assoc in filtered if assoc.label == edge_label]:
                sub_violations.add(
                    DataViolation(
                        name="Link Association Violation",
                        path=f"edges.{index}",
                        schema_type=schema_type,
                        violation_type="warning",
                        message=f"Invalid edge name {edge_label} for edge {src_label} -> {dst_label} ",
                    )
                )
        violations[resource] = sub_violations
    return violations


class ValidatorFactory:
    def __init__(self, data_dir: str, register_defaults: bool = False):

        self.data_dir = data_dir
        self.validators: List[Validator] = []

        if register_defaults:
            self.__register_defaults()

    def register_validator(self, validator: Validator) -> None:
        self.validators.append(validator)

    def register_validator_type(self, validator_type: ValidatorType) -> None:
        validators = VALIDATORS[validator_type]
        for validator in validators:
            self.register_validator(validator)

    def __register_defaults(self) -> None:
        self.register_validator(schema_validator)
        self.register_validator(duplicate_definition_validator)
        self.register_validator(undefined_link_validator)
        self.register_validator(association_validator)

    def validate(
        self, resource_name: str, resource_type: DictionaryType = "GPAS"
    ) -> Dict[str, Set[DataViolation]]:
        payload = load_all(self.data_dir, resource_name)

        violations: Dict[str, Set[DataViolation]] = {}

        for validator in self.validators:
            sub_violations = validator(payload, resource_type)

            for resource, sub_violation in sub_violations.items():
                if resource in violations:
                    violations[resource].update(sub_violation)
                else:
                    violations[resource] = sub_violation
        return violations


def validate_schema(obj: SchemaData, schema_type: DictionaryType = "GPAS") -> Set[DataViolation]:
    ver = f"schema/{schema_type.lower()}.json"

    if schema_type not in SCHEMA:
        with pkg_resources.resource_stream(__name__, ver) as stream:
            schema = json.load(stream)
        SCHEMA[schema_type] = Draft7Validator(schema=schema)

    vs = SCHEMA[schema_type]
    violations: Set[DataViolation] = set()
    for e in vs.iter_errors(obj):
        str_path = ".".join([str(entry) for entry in e.path])
        violations.add(
            DataViolation(
                name="Jsonschema Violation",
                path=str_path,
                schema_type=schema_type,
                message=e.message,
            )
        )
    return violations


def schema_validator(
    payload: Dict[str, SchemaData], schema_type: DictionaryType = "GPAS"
) -> Dict[str, Set[DataViolation]]:
    violations: Dict[str, Set[DataViolation]] = {}

    for resource, schema_data in payload.items():
        schema_violations = validate_schema(schema_data, schema_type)
        violations[resource] = schema_violations
    return violations


VALIDATORS: Dict[ValidatorType, List[Validator]] = {
    "ALL": [],
    "SCHEMA": [schema_validator],
    "DATA": [association_validator, undefined_link_validator, duplicate_definition_validator],
}
