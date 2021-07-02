import json
import logging
import os

import jinja2 as j
import yaml

from psqlgml.models import DictionaryType, SchemaData, SchemaType
from psqlgml.resources import merge
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


def write_template(rendered_template: str, file_name: str):
    loaded = json.loads(rendered_template)

    # dump yaml
    yml = f"{file_name}.yaml"
    with open(yml, "w") as s:
        yaml.safe_dump(loaded, s)

    # dump json
    jsn = f"{file_name}.json"
    with open(jsn, "w") as d:
        json.dump(loaded, d, indent=2)


def validate(data_file: str, dictionary: DictionaryType, validators: str):
    vf = ValidatorFactory()


def load_psqml(
    resource_dir: str, file_name: str, resource_type: DictionaryType = "GDC"
) -> SchemaData:
    vf = ValidatorFactory(resource_dir)

    violations = vf.validate(file_name, resource_type)
    if not violations:
        return merge(resource_dir, file_name)
    raise ValueError("Invalid data")


if __name__ == "__main__":
    # generate_schema("schema/0.1.0", SchemaType.GPAS)
    sample = "versioning/gpas_rna_seq.yaml"
    rss_dir = "/home/rogwara/git/graphmanager/tests/data/exports"

    load_psqml(rss_dir, sample, "GPAS")
