from typing import Any, Dict, List, Union

from psqlgml import typings
from psqlgml.typings import Literal, TypedDict

Category = typings.Literal[
    "administrative",
    "analysis",
    "biospecimen",
    "clinical",
    "data",
    "data_bundle",
    "data_file",
    "index_file",
    "metadata_file",
    "notation",
    "qc_bundle",
    "TBD",
]
UniqueFieldType = Literal["node_id", "submitter_id"]


class GmlSchemaProperties(TypedDict):
    description: str
    edges: Dict[str, Any]
    extends: str
    nodes: Dict[str, Any]
    summary: Dict[str, Any]
    unique_field: Dict[str, Any]


class GmlSchema(TypedDict):
    definitions: Dict[str, Dict[str, Any]]
    description: str
    properties: GmlSchemaProperties
    required: List[str]
    type: Literal["object"]
    url: str
    version: str


class _Edge(TypedDict):
    dst: str  # unique id of the destination node
    src: str  # unique id of the source node


class GmlEdge(_Edge, total=False):
    """Dictionary representation of an edge defined in a sample data set"""

    label: str  # dictionary mapped name of the association between the source and the destination nodes
    tag: str  # custom friendly name for this edge


class SystemAnnotation(TypedDict, total=False):
    legacy_tag: bool
    latest: str
    redacted: bool
    release_blocked: bool
    tag: str
    validation_attempted: str
    ver: int


class GmlNode(TypedDict, total=False):
    """Dictionary representation of a generic node defined in a sample data set"""

    node_id: str
    acl: List[str]
    submitter_id: str
    label: str
    props: Dict[str, Union[bool, int, str]]
    properties: Dict[str, Union[bool, int, str]]
    sysans: SystemAnnotation
    system_annotations: SystemAnnotation


class GmlData(TypedDict, total=False):
    """A sample data set with nodes and edges"""

    description: str
    edges: List[GmlEdge]
    extends: str
    mock_all_props: bool
    nodes: List[GmlNode]
    summary: Dict[str, int]
    unique_field: UniqueFieldType


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


class DictionarySchema(typings.TypedDict):
    """A dictionary representation of an actual node data structure schema definition"""

    id: str
    title: str
    namespace: str
    category: Category
    submittable: bool
    downloadable: bool
    previous_version_downloadable: bool
    description: str
    links: List[SubGroupedLink]
    properties: Dict[str, Any]
    required: List[str]
    systemProperties: List[str]
    tagProperties: List[str]
    uniqueKeys: List[List[str]]


ValidatorType = Literal["ALL", "DATA", "SCHEMA"]
RenderFormat = Literal["jpeg", "pdf", "png"]
