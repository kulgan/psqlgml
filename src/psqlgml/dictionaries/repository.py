import abc
import logging
import os
from pathlib import Path
from typing import Optional

import attr
from dulwich import objects, porcelain

__all__ = ["Repository", "LocalRepository", "GitRepository"]

from psqlgml.dictionaries import schemas

logger = logging.getLogger(__name__)


@attr.s(auto_attribs=True)
class Repository(abc.ABC):
    name: str

    def get_dictionary_directory(self, version: str) -> Path:
        """Local directory where dictionary files will be dumped"""
        dict_home = os.getenv("GML_DICTIONARY_HOME", f"{Path.home()}/.gml/dictionaries")
        return Path(f"{dict_home}/{self.name}/{version}")

    @abc.abstractmethod
    def read(self, version: str) -> schemas.Dictionary:
        """Reads the specified dictionary version from the repository"""


@attr.s(auto_attribs=True)
class LocalRepository(Repository):
    base_directory: Optional[Path] = None

    def get_dictionary_directory(self, version: str) -> Path:
        base_dir = self.base_directory or Path(
            f"{os.getenv('GML_DICTIONARY_HOME', f'{Path.home()}/.gml/dictionaries')}"
        )
        return Path(f"{base_dir}/{self.name}/{version}")

    def read(self, version: str) -> schemas.Dictionary:
        dict_path = self.get_dictionary_directory(version)

        if not dict_path.exists():
            logger.info(f"No local dictionary with name: {self.name}, version: {version} found")
            raise IOError(f"No local dictionary found with name: {self.name}, version: {version}")

        return schemas.Dictionary(
            name=self.name,
            version=version,
            url=str(dict_path),
            schema=schemas.load_schemas(str(dict_path)),
        )


@attr.s(auto_attribs=True)
class GitRepository(Repository):
    url: str
    force: bool = False
    is_tag: bool = True
    origin: bytes = b"origin"
    schema_path: str = "gdcdictionary/schemas"
    repo: porcelain.BaseRepo = None
    lazy_load: bool = False

    def __attrs_post_init__(self) -> None:
        if not self.lazy_load:
            self.clone()

    @property
    def local_directory(self) -> Path:
        git_home = os.getenv("GML_GIT_HOME", f"{Path.home()}/.gml/git")
        local_dir = Path(f"{git_home}/{self.name}")
        local_dir.mkdir(parents=True, exist_ok=True)
        return local_dir

    @property
    def is_cloned(self) -> bool:
        return os.path.exists("{}/.git".format(self.local_directory))

    def get_commit_ref(self, version: str) -> str:
        if self.is_tag:
            return f"refs/tags/{version}"
        return f"refs/remotes/{self.origin.decode()}/{version}"

    def read(self, version: str) -> schemas.Dictionary:
        self.clone()

        commit_id = self.get_commit_id(self.get_commit_ref(version))
        dictionary_dir = self.get_dictionary_directory(version)

        if dictionary_dir.exists() and not self.force:
            return schemas.Dictionary(
                url=self.url,
                name=self.name,
                version=version,
                schema=schemas.load_schemas(str(dictionary_dir)),
            )

        dictionary_dir.mkdir(parents=True, exist_ok=True)
        commit_tree: objects.Tree = porcelain.get_object_by_path(
            self.repo, self.schema_path, committish=commit_id
        )

        # dump schema files to dump location
        for entry in commit_tree.items():

            file_name = entry.path.decode()
            blob = self.repo.get_object(entry.sha)

            # skip sub folders
            if not isinstance(blob, objects.Blob):
                logger.debug(f"Skipping extra folders in schema directory {file_name}")
                continue

            with open(f"{dictionary_dir}/{file_name}", "wb") as f:
                f.write(blob.as_raw_string())
        return schemas.Dictionary(
            url=self.url,
            name=self.name,
            version=version,
            schema=schemas.load_schemas(str(dictionary_dir)),
        )

    def get_commit_id(self, commit_ref: str) -> bytes:
        obj: objects.ShaFile = porcelain.parse_object(self.repo, commit_ref)
        if isinstance(obj, objects.Commit):
            return obj.id
        if isinstance(obj, objects.Tag):
            return obj.object[1]

    def clone(self) -> None:

        if self.repo:
            return

        if not self.is_cloned:
            logger.debug(f"cloning new repository {self.url} into {self.local_directory}")

            self.repo = porcelain.clone(
                self.url,
                target=self.local_directory,
                depth=1,
                checkout=False,
                origin=self.origin.decode(),
            )
        else:
            self.repo = porcelain.Repo(self.local_directory)
