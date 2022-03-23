import abc
import logging
import os
from pathlib import Path
from typing import Optional

from psqlgml.dictionaries import repo, schemas

__all__ = ["load", "load_local", "DictionaryReader"]

logger = logging.getLogger(__name__)
GML_DICTIONARIES_HOME = Path(os.getenv("GML_DICTIONARY_HOME", f"{Path.home()}/.gml/dictionaries"))


if not GML_DICTIONARIES_HOME.exists():
    GML_DICTIONARIES_HOME.mkdir(parents=True, exist_ok=True)


class SchemaReader(abc.ABC):
    """Abstract reader for reading GDC compliant dictionaries"""

    def __init__(self, name: str, version: str) -> None:
        self.name = name
        self.version = version

    @abc.abstractmethod
    def read(self) -> schemas.Dictionary:
        """Read Dictionary based on specific requirements"""


class LocalReader(SchemaReader):
    """Builder for local dictionary schema data"""

    def __init__(self, name: str, version: str, local_dir: Optional[Path] = None) -> None:
        super().__init__(name, version)
        self.local_dir = local_dir or GML_DICTIONARIES_HOME

    def read(self) -> schemas.Dictionary:
        """Read dictionary from a local directory"""

        dict_path = Path(f"{self.local_dir}/{self.name}/{self.version}")

        if not dict_path.exists():
            logger.info(
                f"No local dictionary with name: {self.name}, version: {self.version} found"
            )
            raise IOError("No local dictionary found")

        return schemas.Dictionary(
            name=self.name,
            version=self.version,
            url=str(dict_path),
            schema=schemas.load_schemas(str(dict_path)),
        )


class GitReader(SchemaReader):
    """Builder for reading dictionary schema from git repository"""

    def __init__(self, checkout: repo.RepoCheckout) -> None:
        super().__init__(checkout.repo.name, checkout.commit)
        self.cmd = checkout

    def read(self) -> schemas.Dictionary:
        dict_path = repo.checkout(self.cmd)
        return schemas.Dictionary(
            url=self.cmd.repo.remote_git_url,
            name=self.name,
            version=self.version,
            schema=schemas.load_schemas(dict_path),
        )


class DictionaryReader:
    def __init__(self, name: str, version: str) -> None:
        self.name = name
        self.version = version

        self._git_cmd: Optional[repo.RepoCheckout] = None
        self.reader: Optional[SchemaReader] = None

    def local_dir(self, dir_path: Path) -> "DictionaryReader":
        self.reader = LocalReader(
            name=self.name,
            version=self.version,
            local_dir=dir_path,
        )
        return self

    def git_repo(
        self, url: str, overwrite: bool, schema_path: str = "gdcdictionary/schemas"
    ) -> "DictionaryReader":
        meta = repo.RepoMeta(remote_git_url=url, name=self.name)
        co_cmd = repo.RepoCheckout(
            repo=meta, path=schema_path, commit=self.version, override=overwrite
        )
        self.reader = GitReader(checkout=co_cmd)
        return self

    def read(self) -> schemas.Dictionary:
        return self.reader.read()


def load_local(
    name: str, version: str, dictionary_location: Optional[str] = None
) -> schemas.Dictionary:
    """Attempts to load a previously downloaded dictionary from a local location

    Args:
        name: name/label used to save the dictionary locally
        version: version number of the saved dictionary
        dictionary_location: base directory where all dictionaries are dumped
    Returns:
        A Dictionary instance if dictionary files were previously downloaded, else None
    """
    return DictionaryReader(name, version).local_dir(Path(dictionary_location)).read()


def load(
    version: str,
    overwrite: bool = False,
    name: str = "gdcdictionary",
    schema_path: str = "gdcdictionary/schemas",
    git_url: str = "https://github.com/NCI-GDC/gdcdictionary.git",
) -> schemas.Dictionary:
    """Downloads and loads a dictionary instance based on the input parameters

    Args:
        version: dictionary version number
        overwrite: force a re-download of the dictionary files, defaults to false
        name: name/label used to save the dictionary locally, defaults to gdcdictionary
        schema_path: path to the dictionary files with the dictionary git repository
        git_url: URL to the git repository
    Returns:
        A Dictionary instance
    """

    return (
        DictionaryReader(name, version)
        .git_repo(
            url=git_url,
            overwrite=overwrite,
            schema_path=schema_path,
        )
        .read()
    )
