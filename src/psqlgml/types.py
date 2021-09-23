from typing import Any, Dict, List, Union

import attr

from psqlgml import typings
from psqlgml.typings import Literal, TypedDict

__all__ = [
    "Category",
    "GmlData",
    "GmlEdge",
    "GmlNode",
    "GmlSchema",
    "RenderFormat",
    "DictionarySchema",
    "DictionarySchemaDict",
    "SystemAnnotation",
    "UniqueFieldType",
    "ValidatorType",
]

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
ValidatorType = Literal["ALL", "DATA", "SCHEMA"]
RenderFormat = Literal["jpeg", "pdf", "png"]


class GmlSchemaProperties(TypedDict):
    description: str
    edges: Dict[str, Any]
    extends: str
    nodes: Dict[str, Any]
    summary: Dict[str, Any]
    unique_field: Dict[str, Any]


class GmlSchema(TypedDict):
    """GraphML schema container"""

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
    sysan: SystemAnnotation
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


class DictionarySchemaDict(typings.TypedDict):
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
    program: str
    project: str
    systemProperties: List[str]
    tagProperties: List[str]
    uniqueKeys: List[List[str]]
    validators: str


@attr.s(auto_attribs=True)
class DictionarySchema:
    raw: DictionarySchemaDict

    @property
    def id(self) -> str:
        return self.raw["id"]

    @property
    def title(self) -> str:
        return self.raw["title"]

    @property
    def namespace(self) -> str:
        return self.raw["namespace"]

    @property
    def category(self) -> Category:
        return self.raw["category"]

    @property
    def submittable(self) -> bool:
        return self.raw["submittable"]

    @property
    def downloadable(self) -> bool:
        return self.raw["downloadable"]

    @property
    def previous_version_downloadable(self) -> bool:
        return self.raw["previous_version_downloadable"]

    @property
    def description(self) -> str:
        return self.raw["description"]

    @property
    def system_properties(self) -> List[str]:
        return self.raw["systemProperties"]

    @property
    def links(self) -> List[SubGroupedLink]:
        return self.raw.get("links") or []

    @property
    def required(self) -> List[str]:
        return self.raw["required"]

    @property
    def unique_keys(self) -> List[List[str]]:
        return self.raw["uniqueKeys"]

    @property
    def properties(self) -> Dict[str, Any]:
        return self.raw["properties"]
