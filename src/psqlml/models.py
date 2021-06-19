from typing import Any, Dict, Final, List, Literal, Optional, TypedDict

NODE_ID: Final = "node_id"
UNIQUE_FIELD_TYPE = Literal["node_id", "submitter_id"]


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


class Schema(TypedDict, total=False):
    description: str
    edges: List[Edge]
    extends: str
    model: Optional[Literal["GDC", "GPAS"]]
    nodes: List[Node]
    summary: Dict[str, int]
    unique_field: Optional[UNIQUE_FIELD_TYPE]
