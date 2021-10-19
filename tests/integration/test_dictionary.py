from pathlib import Path

import pytest

from psqlgml import dictionary, repository

pytestmark = [pytest.mark.slow, pytest.mark.dictionary]
REMOTE_GIT_URL = "https://github.com/NCI-GDC/gdcdictionary.git"


@pytest.fixture()
def dictionary_path() -> Path:
    repo = repository.RepoMeta(remote_git_url=REMOTE_GIT_URL, name="smiths")
    command = repository.RepoCheckout(repo=repo, path="gdcdictionary/schemas", commit="2.3.0")

    chk_dir = Path(repository.checkout(command))
    assert chk_dir.exists()
    return chk_dir


def test_remote_dictionary(remote_dictionary) -> None:
    assert len(remote_dictionary.links) == 92
    assert len(remote_dictionary.all_associations()) == 360

    assert {"diagnosis", "project"}.issubset(
        {link.dst for link in remote_dictionary.associations("case")}
    )
    assert {"analyte", "annotation", "file"}.issubset(
        {link.dst for link in remote_dictionary.associations("aliquot")}
    )


def test_dictionary_loading(dictionary_path) -> None:
    d1 = dictionary.load_local(version="2.3.0", name="gdcdictionary")
    assert d1.schema
    assert len(d1.schema) == 81
    program = d1.schema["program"]

    assert program.id == "program"
    assert program.category == "administrative"
    assert program.downloadable is False
    assert program.required
