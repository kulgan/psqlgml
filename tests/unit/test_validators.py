from psqlgml import resources, validators


def test_schema_validator__valid(data_dir: str):
    payload = resources.load_all(data_dir, "simple_valid.json")
    violations = validators.schema_validator(payload, "GPAS")
    assert len(violations["simple_valid.json"]) == 0


def test_schema_validator__invalid(data_dir: str):
    payload = resources.load_all(data_dir, "invalid/invalid.yaml")
    violations = validators.schema_validator(payload, "GDC")
    assert len(violations) == 2

    sub_violations = violations["invalid/invalid.yaml"]
    assert len(sub_violations) == 2
    paths = set(sb.path for sb in sub_violations)
    assert {"nodes.0", "nodes.1"} == paths
