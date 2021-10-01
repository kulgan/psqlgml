from typing import Callable, Set

import pytest

from psqlgml import dictionary, types, typings, validators

pytestmark = [pytest.mark.validation]


class CreateValidationRequest(typings.Protocol):
    def __call__(self, data_file: str) -> validators.ValidationRequest:
        ...


@pytest.fixture()
def validation_request(
    data_dir: str, local_dictionary: dictionary.Dictionary, test_schema: types.GmlSchema
) -> Callable[[str], validators.ValidationRequest]:
    def create_request(data_file: str) -> validators.ValidationRequest:
        return validators.ValidationRequest(
            data_dir=data_dir,
            data_file=data_file,
            schema=test_schema,
            dictionary=local_dictionary,
        )

    return create_request


def test_schema_validator__valid(validation_request: CreateValidationRequest) -> None:
    request = validation_request(data_file="simple_valid.json")
    validator = validators.SchemaValidator(request=request)

    violations = validator.validate()
    assert len(violations["simple_valid.json"]) == 0


def test_schema_validator__invalid(validation_request: CreateValidationRequest) -> None:
    request = validation_request(data_file="invalid/invalid.yaml")
    validator = validators.SchemaValidator(request=request)

    violations = validator.validate()
    assert len(violations) == 2

    sub_violations = violations["invalid/invalid.yaml"]
    assert len(sub_violations) == 2
    assert {"Jsonschema Violation"} == {sb.name for sb in sub_violations}
    assert {"nodes.0", "nodes.1"} == {sb.path for sb in sub_violations}


def test_duplicate_definition_validator(validation_request: CreateValidationRequest) -> None:
    request = validation_request(data_file="invalid/duplicated_def.yaml")
    validator = validators.DuplicateDefinitionValidator(request=request)

    violations = validator.validate()
    all_violations: Set[validators.DataViolation] = set.union(*violations.values())
    assert len(all_violations) == 2
    assert {"nodes.0", "nodes.1"} == {sb.path for sb in all_violations}
    assert {"Duplicate Definition Violation"} == {sb.name for sb in all_violations}


def test_undefined_link_validator(validation_request: CreateValidationRequest) -> None:
    request = validation_request(data_file="invalid/undefined_link.yaml")
    validator = validators.UndefinedLinkValidator(request=request)

    violations = validator.validate()
    all_violations: Set[validators.DataViolation] = set.union(*violations.values())
    assert len(all_violations) == 1
    v = all_violations.pop()
    assert v.level == "warning"
    assert v.name == "Undefined Link Violation"
    assert v.path == "edges.0"


def test_association_validator(validation_request: CreateValidationRequest) -> None:
    request = validation_request(data_file="invalid/association.yaml")
    validator = validators.AssociationValidator(request=request)

    violations = validator.validate()
    vs_1 = violations["simple_valid.yaml"]
    assert len(vs_1) == 1
    v_1 = vs_1.pop()
    assert v_1.level == "warning"
    assert v_1.name == "Link Association Violation"
    assert v_1.path == "edges.0"

    vs_2 = violations["simple_valid.json"]
    assert len(vs_2) == 0

    vs_3 = violations["invalid/association.yaml"]
    assert len(vs_3) == 3


@pytest.mark.parametrize("validator", ["ALL", "SCHEMA", "DATA"])
def test_validation_factory(
    validation_request: CreateValidationRequest, validator: types.ValidatorType
) -> None:
    request = validation_request(data_file="invalid/association.yaml")

    violations = validators.validate(request, validator, print_error=True)
    for file_name, sub_violations in violations.items():
        if file_name == "simple_valid.json":
            assert len(sub_violations) == 0
