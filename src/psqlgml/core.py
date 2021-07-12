import json
import logging
import os

import colored
import jinja2 as j
import yaml

from psqlgml.models import SchemaData, SchemaType
from psqlgml.resources import merge
from psqlgml.typings import DictionaryType, ValidatorType
from psqlgml.validators import ValidatorFactory

logger = logging.getLogger(__name__)

env = j.Environment(
    loader=j.PackageLoader("psqlgml"),
    autoescape=j.select_autoescape(),
    trim_blocks=True,
    lstrip_blocks=True,
)


def generate_schema(
    output_location: str,
    dictionary: DictionaryType = "GDC",
    template_name: str = "schema.jinja",
) -> str:
    template = env.get_template(template_name)
    schema_type = SchemaType.from_value(dictionary.upper())
    rendered = template.render(
        schema=schema_type.value, model=schema_type.name, links=schema_type.links
    )

    os.makedirs(output_location, exist_ok=True)

    output_name = f"{output_location}/{dictionary.lower()}"
    write_template(rendered, output_name)
    return output_name


def write_template(rendered_template: str, file_name: str) -> None:
    loaded = json.loads(rendered_template)

    # dump yaml
    yml = f"{file_name}.yaml"
    with open(yml, "w") as s:
        yaml.safe_dump(loaded, s)

    # dump json
    jsn = f"{file_name}.json"
    with open(jsn, "w") as d:
        json.dump(loaded, d, indent=2)


def validate(
    data_dir: str,
    data_file: str,
    dictionary: DictionaryType,
    validator: ValidatorType = "ALL",
) -> None:
    register_defaults = True if validator == "ALL" else False
    vf = ValidatorFactory(data_dir=data_dir, register_defaults=register_defaults)

    if not register_defaults:
        vf.register_validator_type(validator)

    violations = vf.validate(data_file, dictionary)
    for resource_file, sub_violations in violations.items():
        clr = "red" if sub_violations else "green"
        print(colored.stylize(f"{resource_file}: {dictionary}", colored.fg(clr)))

        for vio in sub_violations:
            error_color = "red" if vio.violation_type == "error" else "yellow"
            print(
                colored.stylize(f"\t{vio.name} - {vio.path}:", colored.fg(error_color)),
                colored.stylize(f"{vio.message}", colored.fg("grey_50")),
            )


def load_psqml(
    resource_dir: str, file_name: str, resource_type: DictionaryType = "GDC"
) -> SchemaData:
    vf = ValidatorFactory(resource_dir)

    violations = vf.validate(file_name, resource_type)
    if not violations:
        return merge(resource_dir, file_name)
    raise ValueError("Invalid data")
