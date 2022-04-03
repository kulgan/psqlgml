import pytest

from psqlgml.dictionaries import repository

pytestmark = [pytest.mark.slow, pytest.mark.dictionary]
REMOTE_GIT_URL = "https://github.com/NCI-GDC/gdcdictionary.git"


def test_clone_git_repo() -> None:
    rm = repository.GitRepository(url=REMOTE_GIT_URL, name="smiths")
    rm.clone()
    assert rm.is_cloned
    assert rm.repo.head()


@pytest.mark.parametrize(
    "commit, is_tag, ref",
    [
        ("2.4.0", True, b"f7ba557228bc113c92387c4eb6160621d27b53ef"),
        ("2.3.0", True, b"1595aef2484ab6fa6c945950b296c4031c2606fd"),
        ("release/avery", False, b"7107e8116ce6ed8185626570dcba14b46e8e4d27"),
    ],
)
def test_get_git_commit_id(commit: str, is_tag: bool, ref: bytes) -> None:
    rm = repository.GitRepository(url=REMOTE_GIT_URL, name="smiths", is_tag=is_tag)
    rm.clone()

    assert ref == rm.get_commit_id(rm.get_commit_ref(commit))


@pytest.mark.slow
@pytest.mark.parametrize("lazy", [True, False])
def test_read_remote_dictionary(lazy: bool) -> None:
    project = repository.GitRepository(
        url=REMOTE_GIT_URL,
        name="smiths",
        force=True,
        schema_path="gdcdictionary/schemas",
        lazy_load=lazy,
    )
    chk_dir = project.get_dictionary_directory("2.3.0")
    dictionary = project.read("2.3.0")
    assert chk_dir.exists()

    entries = [f.name for f in chk_dir.iterdir()]
    assert "program.yaml" in entries

    assert dictionary.name == "smiths"
    assert dictionary.version == "2.3.0"
