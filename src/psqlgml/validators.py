from abc import ABCMeta, abstractmethod
from typing import Dict, Iterable, List, Set, Type, cast

import attr
import colored
from jsonschema import Draft7Validator

import psqlgml.types
from psqlgml import dictionary, resources, types, typings

__all__ = [
    "AssociationValidator",
    "DataViolation",
    "DuplicateDefinitionValidator",
    "SchemaValidator",
    "UndefinedLinkValidator",
    "validate",
    "Validator",
    "ValidatorFactory",
    "ValidationRequest",
    "ViolationErrorType",
    "ViolationType",
]

SCHEMA: Dict[str, Draft7Validator] = {}
ViolationType = typings.Literal[
    "Link Association Violation",
    "Duplicate Definition Violation",
    "Jsonschema Violation",
    "Undefined Link Violation",
]
ViolationErrorType = typings.Literal["error", "warning"]


@attr.s(auto_attribs=True)
class ValidationRequest:
    data_dir: str
    data_file: str
    schema: types.GmlSchema
    dictionary: dictionary.Dictionary

    _payload: Dict[str, types.GmlData] = attr.ib(default=None)

    @property
    def payload(self) -> Dict[str, types.GmlData]:
        if not self._payload:
            self._payload = resources.load_by_resource(self.data_dir, self.data_file)
        return self._payload


@attr.s(frozen=True, auto_attribs=True)
class DataViolation:
    name: ViolationType
    path: str
    message: str
    dictionary: str
    dictionary_version: str
    level: ViolationErrorType = "error"


class Validator(metaclass=ABCMeta):
    def __init__(self, request: ValidationRequest) -> None:
        self.request = request

    @property
    @abstractmethod
    def violation_type(self) -> ViolationType:
        ...

    @abstractmethod
    def validate(self) -> Dict[str, Set[DataViolation]]:
        ...

    @property
    def dictionary(self) -> dictionary.Dictionary:
        return self.request.dictionary

    def report_violation(
        self, path: str, message: str, violation_type: ViolationErrorType = "error"
    ) -> DataViolation:
        return DataViolation(
            name=self.violation_type,
            path=path,
            dictionary=self.dictionary.name,
            dictionary_version=self.dictionary.version,
            message=message,
            level=violation_type,
        )


class SchemaValidator(Validator):
    @property
    def violation_type(self) -> ViolationType:
        return "Jsonschema Violation"

    @property
    def dictionary_tag(self) -> str:
        return f"{self.dictionary.name}/{self.dictionary.version}"

    @property
    def validator(self) -> Draft7Validator:
        if self.dictionary_tag not in SCHEMA:
            gml_schema = self.request.schema
            SCHEMA[self.dictionary_tag] = Draft7Validator(schema=gml_schema)
        return SCHEMA[self.dictionary_tag]

    def validate_schema(self, obj: types.GmlData) -> Set[DataViolation]:

        violations: Set[DataViolation] = set()
        for e in self.validator.iter_errors(obj):
            str_path = ".".join([str(entry) for entry in e.path])
            violations.add(self.report_violation(str_path, e.message))
        return violations

    def validate(self) -> Dict[str, Set[DataViolation]]:

        payload = self.request.payload
        violations: Dict[str, Set[DataViolation]] = {}

        for resource, schema_data in payload.items():
            schema_violations = self.validate_schema(schema_data)
            violations[resource] = schema_violations
        return violations


class DuplicateDefinitionValidator(Validator):
    @property
    def violation_type(self) -> ViolationType:
        return "Duplicate Definition Violation"

    def validate(self) -> Dict[str, Set[DataViolation]]:
        """Raises a violation if a given unique_id is re-used while redefining another node"""

        payload = self.request.payload
        uids: Set[str] = set()

        violations: Dict[str, Set[DataViolation]] = {}
        for resource, schema_data in payload.items():
            nodes = schema_data["nodes"]
            unique_field: types.UniqueFieldType = schema_data.get("unique_field", "submitter_id")

            sub_violations: Set[DataViolation] = set()
            for index, node in enumerate(nodes):
                uid = node[unique_field]

                if uid in uids:
                    sub_violations.add(
                        self.report_violation(
                            f"nodes.{index}", f"{unique_field} redefined for {uid}"
                        )
                    )
                uids.add(uid)
            violations[resource] = sub_violations
        return violations


class UndefinedLinkValidator(Validator):
    @property
    def violation_type(self) -> ViolationType:
        return "Undefined Link Violation"

    def validate(self) -> Dict[str, Set[DataViolation]]:
        payload = self.request.payload
        violations: Dict[str, Set[DataViolation]] = {}
        entries: Set[str] = set()
        for resource, schema_data in payload.items():
            unique_field: types.UniqueFieldType = schema_data.get("unique_field", "submitter_id")
            uids = (n[unique_field] for n in schema_data["nodes"])
            entries.update(uids)

        for resource, schema_data in payload.items():
            edges = schema_data["edges"]
            sub_violations: Set[DataViolation] = set()

            for index, edge in enumerate(edges):
                for key in ["src", "dst"]:
                    key = cast(typings.Literal["src", "dst"], key)
                    if edge[key] in entries:
                        continue
                    str_path = f"edges.{index}"
                    message = f"node with unique key value {edge[key]} not defined"
                    sub_violations.add(self.report_violation(str_path, message, "warning"))
            violations[resource] = sub_violations
        return violations


class AssociationValidator(Validator):
    @property
    def violation_type(self) -> ViolationType:
        return "Link Association Violation"

    def validate(self) -> Dict[str, Set[DataViolation]]:
        payload = self.request.payload
        violations: Dict[str, Set[DataViolation]] = {}
        node_types: Dict[str, str] = {}

        for resource, schema in payload.items():
            unique_field: types.UniqueFieldType = schema.get("unique_field", "submitter_id")
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

                associations = self.dictionary.associations(src_label)
                filtered = [assoc for assoc in associations if assoc.dst == dst_label]
                str_path = f"edges.{index}"
                if not filtered:
                    message = f"node type {src_label} cannot be linked to {dst_label} "
                    sub_violations.add(self.report_violation(str_path, message))
                # validate edge label
                if edge_label and not [assoc for assoc in filtered if assoc.name == edge_label]:
                    message = (
                        f"Invalid edge name {edge_label} for edge {src_label} -> {dst_label} "
                    )
                    sub_violations.add(self.report_violation(str_path, message, "warning"))
            violations[resource] = sub_violations
        return violations


@attr.s(auto_attribs=True)
class ValidatorFactory:
    request: ValidationRequest
    register_defaults: bool
    validators: List[Validator] = attr.ib(factory=list)

    def __attrs_post_init__(self) -> None:
        if self.register_defaults:
            self.__register_defaults()

    def register_validator(self, validator_type: Type[Validator]) -> None:
        v = validator_type(request=self.request)
        self.validators.append(v)

    def register_validator_type(self, validator_type: psqlgml.types.ValidatorType) -> None:
        validators = VALIDATORS[validator_type]
        for validator in validators:
            self.register_validator(validator)

    def __register_defaults(self) -> None:
        self.register_validator(SchemaValidator)
        self.register_validator(DuplicateDefinitionValidator)
        self.register_validator(UndefinedLinkValidator)
        self.register_validator(AssociationValidator)

    def validate(self) -> Dict[str, Set[DataViolation]]:
        violations: Dict[str, Set[DataViolation]] = {}

        for validator in self.validators:
            sub_violations = validator.validate()

            for resource, sub_violation in sub_violations.items():
                if resource in violations:
                    violations[resource].update(sub_violation)
                else:
                    violations[resource] = sub_violation
        return violations


VALIDATORS: Dict[str, Iterable[Type[Validator]]] = {
    "ALL": [],
    "SCHEMA": [SchemaValidator],
    "DATA": [AssociationValidator],
}


def validate(
    request: ValidationRequest,
    validator: psqlgml.types.ValidatorType = "ALL",
    print_error: bool = False,
) -> Dict[str, Set[DataViolation]]:
    register_defaults = True if validator == "ALL" else False
    vf = ValidatorFactory(
        request=request,
        register_defaults=register_defaults,
    )

    if not register_defaults:
        vf.register_validator_type(validator)

    violations = vf.validate()
    if print_error:
        print_violations(violations, request.dictionary)
    return violations


def print_violations(violations: Dict[str, Set[DataViolation]], d: dictionary.Dictionary) -> None:
    for resource_file, sub_violations in violations.items():
        clr = "red" if sub_violations else "green"
        print(
            colored.stylize(f"{resource_file}: {d.name}, version: {d.version}", colored.fg(clr))
        )

        errors: int = 0
        warnings: int = 0
        error_color = "green"

        for vio in sub_violations:
            if vio.level == "error":
                errors += 1
                error_color = "red"
            if vio.level == "warning":
                warnings += 1
                error_color = "yellow"
            print(
                colored.stylize(f"\t{vio.name} - {vio.path}:", colored.fg(error_color)),
                colored.stylize(f"{vio.message}", colored.fg("grey_50")),
            )
        print(
            colored.stylize(
                f"Summary: {errors} error(s), {warnings} warning(s)",
                colored.fg(clr),
            )
        )
