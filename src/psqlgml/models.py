from typing import Any, Dict, List

from psqlgml.typings import TypedDict, UniqueFieldType


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


class GmlSchema(TypedDict):
    definitions: Dict[str, Dict[str, Any]]
    description: str
    properties: Dict[str, Any]
    required: List[str]
    tagProperties: List[str]
    url: str
    version: str


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
    nodes: List[Node]
    summary: Dict[str, int]
    unique_field: UniqueFieldType
