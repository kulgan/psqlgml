import json
from typing import Dict

import yaml

from psqlgml.models import SchemaData


def load_all(resource_dir: str, resource_name: str) -> Dict[str, SchemaData]:
    schema_data: Dict[str, SchemaData] = {}
    resource_names = {resource_name}

    while resource_names:
        name = resource_names.pop()
        obj = loads(f"{resource_dir}/{name}")
        schema_data[name] = obj

        sub_resource = obj.get("extends")
        if sub_resource:
            resource_names.add(sub_resource)
    return schema_data


def loads(file_name: str) -> SchemaData:
    extension = file_name.split(".")[-1]
    with open(file_name, "r") as r:
        if extension == "json":
            return json.loads(r.read())

        if extension in ["yml", "yaml"]:
            return yaml.safe_load(r)
    return SchemaData()


def merge(resource_folder: str, resource_name: str) -> SchemaData:
    file_name = f"{resource_folder}/{resource_name}"
    rss: SchemaData = loads(file_name)

    extended_resource = rss.pop("extends", None)
    if not extended_resource:
        return rss

    extended = merge(resource_folder, extended_resource)

    # merge
    rss["nodes"] += extended["nodes"]
    rss["edges"] += extended["edges"]

    if "summary" not in rss:
        rss["summary"] = extended.get("summary", {})
        return rss

    for summary in extended.get("summary", {}):
        if summary in rss["summary"]:
            rss["summary"][summary] += extended["summary"][summary]
        else:
            rss["summary"][summary] = extended["summary"][summary]

    return rss
