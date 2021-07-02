import enum
from dataclasses import dataclass
from typing import Any, Dict, Final, List, Literal, Optional, Set, TypedDict

from biodictionary import biodictionary
from gdcdictionary import gdcdictionary

NODE_ID: Final = "node_id"
DictionaryType = Literal["GDC", "GPAS"]
UniqueFieldType = Literal["node_id", "submitter_id"]


class Link(TypedDict, total=False):
    exclusive: bool
    required: bool
    subgroup: List["Link"]
    name: str
    label: str
    target_type: str
    backref: str
    multiplicity: str


class GdcSchema(TypedDict):
    description: str
    links: List[Link]
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
    model: Optional[Literal["GDC", "GPAS"]]
    nodes: List[Node]
    summary: Dict[str, int]
    unique_field: Optional[UniqueFieldType]


@dataclass(frozen=True)
class SchemaViolation:
    path: str
    message: str
    schema_type: DictionaryType
    violation_type: Literal["error", "warning"] = "error"


@dataclass(frozen=True)
class Association:
    src: str
    dst: str
    label: str


class SchemaType(enum.Enum):
    GDC = gdcdictionary.schema
    GPAS = biodictionary.schema

    def extract_association(self, src: str, link: Link) -> Set[Association]:
        associations = set()
        if "name" in link:
            dst = link["target_type"]
            label = link["name"]
            backref = link["backref"]
            associations.add(Association(src, dst, label))
            associations.add(Association(dst, src, backref))
        if "subgroup" in link:
            for sub in link["subgroup"]:
                sub_associations = self.extract_association(src, sub)
                associations.update(sub_associations)
        return associations

    @property
    def links(self) -> Set[str]:
        all_links: Set[str] = set()
        for label, schema in self.value.items():  # type: str, GdcSchema
            links_schema = schema.get("links", [])

            for link in links_schema:
                associations = self.extract_association(label, link)
                all_links.update([assoc.label for assoc in associations])
        return all_links

    def associations(self, label: str) -> Set[Association]:
        label_schema = self.value[label]
        associations = set()
        for link in label_schema.get("links", []):
            associations.update(self.extract_association(label, link))
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
