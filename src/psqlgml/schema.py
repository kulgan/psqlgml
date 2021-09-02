import json
import logging
import os
from pathlib import Path
from typing import Optional

import jinja2 as j
import yaml

from psqlgml import dictionary, resources, types

__all__ = [
    "generate",
    "read",
]

logger = logging.getLogger(__name__)
env = j.Environment(
    loader=j.PackageLoader("psqlgml"),
    autoescape=j.select_autoescape(),
    trim_blocks=True,
    lstrip_blocks=True,
)


def generate(
    loaded_dictionary: dictionary.Dictionary,
    output_location: Optional[str] = None,
    template_name: str = "schema.jinja2",
) -> str:
    """Creates a new json schema based on specified dictionary"""

    template = env.get_template(template_name)
    output_location = output_location or os.getenv(
        "GML_SCHEMA_HOME", f"{Path.home()}/.gml/schemas"
    )

    rendered = template.render(
        schema=loaded_dictionary.schema,
        git_url=loaded_dictionary.url,
        git_version=loaded_dictionary.version,
        links=loaded_dictionary.links,
    )

    output_location = f"{output_location}/{loaded_dictionary.name}/{loaded_dictionary.version}"
    os.makedirs(output_location, exist_ok=True)

    output_name = f"{output_location}/schema"
    write_template(rendered, output_name)
    return output_name


def write_template(rendered_template: str, file_name: str) -> None:
    loaded = json.loads(rendered_template)

    # dump yaml
    yml = f"{file_name}.yaml"
    print(yml)
    with open(yml, "w") as s:
        yaml.safe_dump(loaded, s)

    # dump json
    jsn = f"{file_name}.json"
    with open(jsn, "w") as d:
        json.dump(loaded, d, indent=2)


def read(name: str, version: str, schema_location: Optional[str] = None) -> types.GmlSchema:
    """Loads a dictionary schema into memory for use in validation"""

    schema_location = schema_location or os.getenv(
        "GML_SCHEMA_HOME", f"{Path.home()}/.gml/schemas"
    )
    target_schema = Path(f"{schema_location}/{name}/{version}/schema.json")
    if not target_schema.exists():
        logger.error(f"Specified dictionary file not found at {target_schema}")
        raise ValueError(
            f"Dictionary schema not found at {target_schema}, you can generate it using the generat command"
        )

    resource_file = resources.ResourceFile[types.GmlSchema](str(target_schema))
    return resource_file.read()
