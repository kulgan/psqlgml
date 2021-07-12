import enum
from functools import lru_cache
from typing import Any, Dict, List, Set, cast

import attr
from biodictionary import biodictionary
from gdcdictionary import gdcdictionary

from psqlgml.typings import Literal, TypedDict, UniqueFieldType


class Link(TypedDict):
    exclusive: bool
    required: bool
    name: str
    label: str
    target_type: str
    backref: str
    multiplicity: str


class SubGroupedLink(Link, total=False):
    subgroup: List[Link]


class GdcSchema(TypedDict):
    description: str
    links: List[SubGroupedLink]
    properties: Dict[str, Any]
    required: List[str]
    systemProperties: List[str]
    tagProperties: List[str]


class Edge(TypedDict, total=False):
    dst: str
    label: str
    src: str
    tag: str


class Node(TypedDict, total=False):
    node_id: str
    submitter_id: str
    label: str


class SchemaData(TypedDict, total=False):
    description: str
    edges: List[Edge]
    extends: str
    model: Literal["GDC", "GPAS"]
    nodes: List[Node]
    summary: Dict[str, int]
    unique_field: UniqueFieldType


@attr.s(frozen=True, auto_attribs=True)
class Association:
    src: str
    dst: str
    label: str


def extract_association(src: str, link: SubGroupedLink) -> Set[Association]:
    associations = set()
    links: List[SubGroupedLink] = [link]

    while links:
        current = links.pop()
        if "name" in current:
            dst = current["target_type"]
            label = current["name"]
            backref = current["backref"]
            associations.add(Association(src, dst, label))
            associations.add(Association(dst, src, backref))
        if "subgroup" in current:
            for sub in current["subgroup"]:
                links.append(cast(SubGroupedLink, sub))

    return associations


class SchemaType(enum.Enum):
    GDC = gdcdictionary.schema
    GPAS = biodictionary.schema

    @property
    def links(self) -> Set[str]:
        all_links: Set[str] = set()
        for label in self.value:  # type: str
            associations = self.associations(label)
            all_links.update([assoc.label for assoc in associations])
        return all_links

    def associations(self, label: str) -> Set[Association]:
        return {a for a in self.all_associations() if a.src == label}

    @lru_cache(maxsize=1)
    def all_associations(self) -> Set[Association]:
        associations: Set[Association] = set()
        for label, label_schema in self.value.items():
            for link in label_schema.get("links", []):
                associations.update(extract_association(label, link))
        return associations

    @property
    def value(self) -> Dict[str, GdcSchema]:
        return self._value_

    @classmethod
    def from_value(cls, value: str) -> "SchemaType":
        for name, member in cls.__members__.items():
            if name == value:
                return member
        raise ValueError(f"Unknown schema type {value}")
