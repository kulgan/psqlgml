from typing import Dict, cast

import attr
import pkg_resources
import yaml

from psqlgml import types


@attr.s(auto_attribs=True)
class SchemaInfo:
    name: str
    version: str
    source_dir: str


def _load_dictionary(name: str) -> Dict[str, types.DictionarySchemaDict]:
    with pkg_resources.resource_stream(__name__, name) as f:
        return cast(types.DictionarySchemaDict, yaml.safe_load(f))


class Dictionary:
    def __init__(self, name) -> None:
        self.schema: Dict[str, types.DictionarySchemaDict] = _load_dictionary(name)


MiniDictionary = Dictionary("data/dictionary/mini.yaml")
