import json
from typing import Dict, Generic, TypeVar, cast

import attr
import yaml

from psqlgml.types import GmlData

__all__ = [
    "load_resource",
    "load_by_resource",
    "ResourceFile",
]

T = TypeVar("T")


def load_by_resource(resource_dir: str, resource_name: str) -> Dict[str, GmlData]:
    """Loads all resources reference within the input resource and returns a mapping
    with each resource having an entry.
    For example, if the main resource extends another resource which does not extend
    anything, this function will return two entries, one for each resource
    """
    schema_data: Dict[str, GmlData] = {}
    resource_names = {resource_name}

    while resource_names:
        name = resource_names.pop()
        f = ResourceFile[GmlData](f"{resource_dir}/{name}")
        obj = f.read()
        schema_data[name] = obj

        sub_resource = obj.get("extends")
        if sub_resource:
            resource_names.add(sub_resource)
    return schema_data


def load_resource(resource_folder: str, resource_name: str) -> GmlData:
    """Loads all data resource files into a single Gml Data instance"""

    file_name = f"{resource_folder}/{resource_name}"
    f = ResourceFile[GmlData](file_name)
    rss: GmlData = f.read()

    extended_resource = rss.pop("extends", None)
    if not extended_resource:
        return rss

    extended = load_resource(resource_folder, extended_resource)

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


@attr.s(frozen=True, auto_attribs=True)
class ResourceFile(Generic[T]):
    absolute_name: str

    @property
    def extension(self) -> str:
        return self.absolute_name.split(".")[-1]

    def read(self) -> T:
        loaded: T
        with open(self.absolute_name, "r") as r:
            if self.extension == "json":
                loaded = cast(T, json.loads(r.read()))

            if self.extension in ["yml", "yaml"]:
                loaded = cast(T, yaml.safe_load(r))
        return loaded
