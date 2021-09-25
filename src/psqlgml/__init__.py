from pkg_resources import get_distribution

from psqlgml.dictionary import Association, Dictionary, from_object, load, load_local
from psqlgml.resources import ResourceFile, load_by_resource, load_resource
from psqlgml.schema import generate
from psqlgml.schema import read as read_schema
from psqlgml.types import (
    DictionarySchema,
    DictionarySchemaDict,
    GmlData,
    GmlEdge,
    GmlNode,
    GmlSchema,
    SystemAnnotation,
)
from psqlgml.validators import DataViolation, ValidationRequest, validate
from psqlgml.visualization import draw

VERSION = get_distribution(__name__).version

__all__ = [
    "Association",
    "DataViolation",
    "Dictionary",
    "DictionarySchema",
    "DictionarySchemaDict",
    "GmlData",
    "GmlEdge",
    "GmlSchema",
    "ResourceFile",
    "SystemAnnotation",
    "ValidationRequest",
    "draw",
    "generate",
    "load",
    "load_by_resource",
    "load_local",
    "load_resource",
    "from_object",
    "read_schema",
    "validate",
]
