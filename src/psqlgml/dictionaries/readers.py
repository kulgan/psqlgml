import logging
import os
from pathlib import Path
from typing import Optional, Union, cast

from psqlgml.dictionaries import repository, schemas

__all__ = ["load", "load_local", "DictionaryReader"]

logger = logging.getLogger(__name__)


class DictionaryReader:
    def __init__(self, name: str, version: str) -> None:
        self.name = name
        self.version = version

        self._url: Optional[str] = None
        self._is_tag: bool = True
        self._overwrite: bool = False
        self._schema_path: str = "gdcdictionary/schemas"
        self._base_dir: Path = Path(
            os.getenv("GML_DICTIONARY_HOME", f"{Path.home()}/.gml/dictionaries")
        )

        self.reader: Optional[repository.Repository] = None

    def local(self, base_directory: Optional[Union[str, Path]] = None) -> "DictionaryReader":
        base_directory = (
            Path(base_directory) if isinstance(base_directory, str) else base_directory
        )
        logger.debug(f"Reading local Dictionary {self.name}: {self.version} @ {base_directory}")
        self._base_dir = base_directory or self._base_dir
        return self

    def git(
        self,
        url: str,
        overwrite: bool,
        schema_path: str = "gdcdictionary/schemas",
        is_tag: bool = True,
    ) -> "DictionaryReader":
        logger.debug(f"Reading remote Dictionary {self.name}: {self.version} @ {url}")

        self._url = url
        self._is_tag = is_tag
        self._overwrite = overwrite
        self._schema_path = schema_path
        return self

    def is_preloaded_dictionary(self) -> bool:
        """Checks if a dictionary with name and version has been previously loaded"""
        return Path(f"{self._base_dir}/{self.name}/{self.version}").exists()

    def read(self) -> schemas.Dictionary:
        if self.is_preloaded_dictionary() and not self._overwrite:
            return repository.LocalRepository(name=self.name, base_directory=self._base_dir).read(
                self.version
            )
        return repository.GitRepository(
            name=self.name,
            url=cast(str, self._url),
            schema_path=self._schema_path,
            force=self._overwrite,
            is_tag=self._is_tag,
        ).read(self.version)


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
    base_path = Path(dictionary_location) if dictionary_location else None
    return DictionaryReader(name, version).local(base_path).read()


def load(
    version: str,
    overwrite: bool = False,
    name: str = "gdcdictionary",
    schema_path: str = "gdcdictionary/schemas",
    git_url: str = "https://github.com/NCI-GDC/gdcdictionary.git",
    is_tag: bool = True,
) -> schemas.Dictionary:
    """Downloads and loads a dictionary instance based on the input parameters

    Args:
        version: dictionary version number
        overwrite: force a re-download of the dictionary files, defaults to false
        name: name/label used to save the dictionary locally, defaults to gdcdictionary
        schema_path: path to the dictionary files with the dictionary git repository
        git_url: URL to the git repository
        is_tag: tag or commit
    Returns:
        A Dictionary instance
    """

    return (
        DictionaryReader(name, version)
        .git(
            url=git_url,
            is_tag=is_tag,
            overwrite=overwrite,
            schema_path=schema_path,
        )
        .read()
    )
