from pathlib import Path

import pkg_resources
import pytest

from psqlgml.dictionaries import repository


@pytest.mark.parametrize(
    "default_base, expectation",
    [
        (True, f"{Path.home()}/.gml/dictionaries/dictionary/0.1.0"),
        (False, f"{pkg_resources.resource_filename('tests', 'data')}/dictionary/0.1.0"),
    ],
)
def test_get_local_dictionary_dir(data_dir: str, default_base: bool, expectation: str) -> None:
    """Tests initializing a Local repository"""

    base_dir = None if default_base else Path(data_dir)
    repo = repository.LocalRepository(name="dictionary", base_directory=base_dir)

    assert repo.name == "dictionary"
    assert Path(expectation) == repo.get_dictionary_directory("0.1.0")


def test_load_local_dictionary(data_dir: str) -> None:
    base_dir = Path(data_dir)
    repo = repository.LocalRepository(name="dictionary", base_directory=base_dir)
    dictionary = repo.read("0.1.0")
    assert dictionary
    assert dictionary.name == "dictionary"
    assert dictionary.version == "0.1.0"


def test_load_invalid_local_dictionary(data_dir: str) -> None:
    base_dir = Path(data_dir)
    repo = repository.LocalRepository(name="dictionary", base_directory=base_dir)
    with pytest.raises(IOError) as exc_info:
        repo.read("0.2.0")
    assert exc_info.type == IOError
    assert (
        exc_info.value.args[0]
        == "No local dictionary found with name: dictionary, version: 0.2.0"
    )
