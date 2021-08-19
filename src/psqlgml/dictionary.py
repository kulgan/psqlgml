import logging
import os
from pathlib import Path
from typing import Any, Dict, FrozenSet, List, Optional, Set, TypeVar, cast

import attr
import yaml
from jsonschema import RefResolver

from psqlgml import repository, typings

logger = logging.getLogger(__name__)

DEFAULT_META_SCHEMA: typings.Final[str] = "metaschema.yaml"
DEFAULT_DEFINITIONS: FrozenSet[str] = frozenset(
    [
        "_definitions.yaml",
        "_terms.yaml",
        "_terms_enum.yaml",
    ]
)

T = TypeVar("T")
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
RESOLVERS: Dict[str, "Resolver"] = {}


class Link(typings.TypedDict):
    exclusive: bool
    required: bool
    name: str
    label: str
    target_type: str
    backref: str
    multiplicity: str


class SubGroupedLink(Link, total=False):
    subgroup: List[Link]


class SchemaDict(typings.TypedDict):
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


@attr.s(auto_attribs=True)
class Schema:
    raw: SchemaDict

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
        return self.raw["links"]

    @property
    def required(self) -> List[str]:
        return self.raw["required"]

    @property
    def unique_keys(self) -> List[List[str]]:
        return self.raw["uniqueKeys"]

    @property
    def properties(self) -> Dict[str, Any]:
        return self.raw["properties"]


@attr.s(auto_attribs=True)
class Resolver:
    name: str
    schema: Dict[str, Any]

    @property
    def ref(self) -> RefResolver:
        return RefResolver(f"{self.name}#", self.schema)

    def resolve(self, reference: str) -> Any:
        base, _ = reference.split("#", 1)
        resolver = RESOLVERS[base] if base else self
        ref = resolver.ref
        _, resolution = ref.resolve(reference)
        return resolve_schema(resolution, resolver)

    def repr(self) -> str:
        return f"{self.__class__.__name__}<{self.name}>"


@attr.s(auto_attribs=True, frozen=True)
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


@attr.s(auto_attribs=True, frozen=True)
class Dictionary:
    url: str
    name: str
    version: str
    schema: Dict[str, Schema]

    @property
    def links(self) -> Set[str]:
        all_links: Set[str] = set()
        for label in self.schema:  # type: str
            associations = self.associations(label)
            all_links.update([assoc.label for assoc in associations])
        return all_links

    def associations(self, label: str) -> Set[Association]:
        return {a for a in self.all_associations() if a.src == label}

    def all_associations(self) -> Set[Association]:
        associations: Set[Association] = set()
        for label, label_schema in self.schema.items():
            for link in label_schema.links:
                associations.update(extract_association(label, link))
        return associations


def load_yaml(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_schemas(
    schema_path: str,
    meta_schema: str = DEFAULT_META_SCHEMA,
    definitions: FrozenSet[str] = DEFAULT_DEFINITIONS,
) -> Dict[str, Schema]:

    excludes: FrozenSet[str] = frozenset([meta_schema] + list(definitions))
    raw_schemas: List[SchemaDict] = []

    definitions_paths = Path(schema_path)
    for definition in definitions_paths.iterdir():
        if definition.is_dir() or definition.name == "README.md":
            continue

        path = definition.name
        schema = load_yaml(definition)
        RESOLVERS[path] = Resolver(name=path, schema=schema)
        if path not in excludes:
            raw_schemas.append(cast(SchemaDict, schema))

    return _load_schema(raw_schemas)


def resolve_schema(entry: T, resolver: Optional[Resolver] = None) -> T:

    # unit entries
    if not isinstance(entry, (list, dict)):
        return entry

    # handle list
    if isinstance(entry, list):
        return cast(T, [resolve_schema(e, resolver) for e in entry])

    resolved: Dict[str, Any] = {}
    for k, v in entry.items():
        if k == "$ref":
            refs = v
            if not isinstance(refs, list):
                refs = [v]

            for ref in refs:
                resolution = resolve_ref(ref, resolver)
                resolved.update(resolution)
        else:
            resolved[k] = resolve_schema(v, resolver)
    return cast(T, resolved)


def resolve_ref(reference: str, resolver: Optional[Resolver] = None) -> Any:
    logger.debug(f"Resolving reference: {reference} with resolver: {resolver}")

    base, _ = reference.split("#", 1)
    if not resolver or (base and resolver.name != base):
        resolver = RESOLVERS[base]
    return resolver.resolve(reference)


def _load_schema(schemas: List[SchemaDict]) -> Dict[str, Schema]:
    loaded: Dict[str, Schema] = {}
    for schema in schemas:
        logger.debug(f"Resolving dictionary schema with id: {schema['id']}")

        raw: SchemaDict = resolve_schema(schema)
        loaded[schema["id"]] = Schema(raw=raw)

        logger.debug(f"Schema resolution complete for schema id: {schema['id']}")
    return loaded


def load(
    version: str,
    overwrite: bool = False,
    name: str = "gdcdictionary",
    schema_path: str = "gdcdictionary/schemas",
    git_path: str = "https://github.com/NCI-GDC/gdcdictionary.git",
    meta_schema: str = DEFAULT_META_SCHEMA,
    definitions: FrozenSet[str] = DEFAULT_DEFINITIONS,
) -> Dictionary:

    local_dictionary = load_local(name, version) if not overwrite else None
    if local_dictionary:
        return local_dictionary

    logger.info(f"Attempting to read dictionary from location {git_path}")
    repo = repository.RepoMeta(remote_git_url=git_path, name=name)
    checkout_command = repository.RepoCheckout(
        repo=repo, path=schema_path, commit=version, override=overwrite
    )
    checkout_dir = repository.checkout(checkout_command)

    logger.info(f"loading dictionary from {checkout_dir}")
    loaded_schema = load_schemas(checkout_dir, meta_schema, definitions)
    return Dictionary(url=git_path, name=name, version=version, schema=loaded_schema)


def load_local(
    name: str, version: str, dictionary_location: Optional[str] = None
) -> Optional[Dictionary]:
    dict_home = os.getenv("GML_DICTIONARY_HOME", f"{Path.home()}/.gml/dictionaries")
    dictionary_location = dictionary_location or dict_home
    directory = Path(f"{dictionary_location}/{name}/{version}")
    if not directory.exists():
        logger.info(f"No local copy of dictionary with name: {name}, version: {version} found")
        return None
    logger.info(f"Attempting to load dictionary from local path {directory}")
    s = load_schemas(str(directory), DEFAULT_META_SCHEMA, DEFAULT_DEFINITIONS)
    return Dictionary(name=name, version=version, schema=s, url=str(directory))
