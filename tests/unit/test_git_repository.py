import os
from pathlib import Path
from unittest import mock

import pkg_resources
import pytest

from psqlgml.dictionaries import repository

REMOTE_GIT_URL = "https://github.com/NCI-GDC/gdcdictionary.git"


@pytest.mark.parametrize(
    "default_base, expectation",
    [
        (True, f"{Path.home()}/.gml/dictionaries/dictionary/0.1.0"),
        (False, f"{pkg_resources.resource_filename('tests', 'data')}/dictionary/0.1.0"),
    ],
)
def test_get_dictionary_dir(data_dir: str, default_base: str, expectation) -> None:
    """Tests dictionary directory is set properly with and without env variables"""

    gml_dir = f"{Path.home()}/.gml/dictionaries" if default_base else data_dir
    with mock.patch.dict(os.environ, {"GML_DICTIONARY_HOME": gml_dir}):

        repo = repository.GitRepository(name="dictionary", url=REMOTE_GIT_URL, lazy_load=True)
        assert repo.name == "dictionary"
        assert Path(expectation) == repo.get_dictionary_directory("0.1.0")


@pytest.mark.parametrize(
    "local_git_home",
    [
        f"{Path.home()}/.gml/git",
        f"{pkg_resources.resource_filename('tests', 'data')}",
    ],
)
def test_get_local_git_dir(local_git_home: str) -> None:
    """Tests dictionary directory is set properly with and without env variables"""

    with mock.patch.dict(os.environ, {"GML_GIT_HOME": local_git_home}):

        repo = repository.GitRepository(name="dictionary", url=REMOTE_GIT_URL, lazy_load=True)
        assert repo.name == "dictionary"
        assert Path(f"{local_git_home}/dictionary") == repo.local_directory


def test_lazy_load_no_clone(tmpdir: Path) -> None:
    with mock.patch.dict(os.environ, {"GML_GIT_HOME": str(tmpdir)}):
        rm = repository.GitRepository(url=REMOTE_GIT_URL, name="smiths", lazy_load=True)
        assert rm.is_cloned is False


@pytest.mark.parametrize(
    "is_tag, expected_ref", [(True, "refs/tags/0.1.0"), (False, "refs/remotes/origin/0.1.0")]
)
def test_get_commit_ref(is_tag: bool, expected_ref: str) -> None:
    rm = repository.GitRepository(
        url=REMOTE_GIT_URL, name="smiths", lazy_load=True, is_tag=is_tag
    )
    assert expected_ref == rm.get_commit_ref("0.1.0")
