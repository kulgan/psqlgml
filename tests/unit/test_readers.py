import os
from pathlib import Path
from unittest import mock

from psqlgml.dictionaries import readers


def test_local_reader(data_dir: str):
    dictionary = readers.DictionaryReader("dictionary", "0.1.0").local(f"{data_dir}").read()
    assert dictionary.name == "dictionary"
    assert dictionary.version == "0.1.0"


def test_load_local(data_dir: str):
    dictionary = readers.load_local("dictionary", "0.1.0", data_dir)
    assert dictionary.name == "dictionary"
    assert dictionary.version == "0.1.0"


def test_remote_reader(data_dir: str, git_server: str, tmpdir: Path) -> None:
    with mock.patch.dict(
        os.environ,
        {"GML_GIT_HOME": f"{tmpdir}/git", "GML_DICTIONARY_HOME": f"{tmpdir}/dictionaries"},
    ):
        dictionary = readers.DictionaryReader("dictionary", "0.1.0").git(git_server, True).read()
        assert dictionary.name == "dictionary"
        assert dictionary.version == "0.1.0"


def test_load_remote(data_dir: str, git_server: str, tmpdir: Path) -> None:
    with mock.patch.dict(
        os.environ,
        {"GML_GIT_HOME": f"{tmpdir}/git", "GML_DICTIONARY_HOME": f"{tmpdir}/dictionaries"},
    ):
        dictionary = readers.load(name="dictionary", version="0.1.0", git_url=git_server)
        assert dictionary.name == "dictionary"
        assert dictionary.version == "0.1.0"
