import enum
import json
import os
from collections.abc import Set

import jinja2 as j
import yaml
from biodictionary import biodictionary
from gdcdictionary import gdcdictionary

from psqlml.models import GdcSchema, Link

env = j.Environment(
    loader=j.PackageLoader("psqlml"),
    autoescape=j.select_autoescape(),
    trim_blocks=True,
    lstrip_blocks=True,
)


class SchemaType(enum.Enum):
    GDC = gdcdictionary.schema
    GPAS = biodictionary.schema

    def extract_links(self, schema: Link) -> Set[str]:
        extracted = set()
        if "name" in schema:
            extracted.add(schema["name"])
            extracted.add(schema["backref"])
        if "subgroup" in schema:
            for s in schema["subgroup"]:
                extracted.update(self.extract_links(s))
        return extracted

    @property
    def links(self) -> Set[str]:
        all_links = set()
        for label, schema in self.value.items():  # type: str, GdcSchema
            links_schema = schema.get("links", [])

            for link in links_schema:
                all_links.update(self.extract_links(link))
        return all_links


def generate_schema(
    output_location: str,
    schema_type: SchemaType = SchemaType.GDC,
    template_name: str = "schema.jinja",
):
    template = env.get_template(template_name)
    rendered = template.render(
        schema=schema_type.value, model=schema_type.name, links=schema_type.links
    )

    os.makedirs(output_location, exist_ok=True)

    output_name = f"{output_location}/{schema_type.name.lower()}"
    write_template(rendered, output_name)


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


if __name__ == "__main__":
    generate_schema("schema/0.1.0", SchemaType.GPAS)
