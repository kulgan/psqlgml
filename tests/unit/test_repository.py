import os
from pathlib import Path
from unittest import mock

from psqlgml import repository

REMOTE_GIT_URL = "https://github.com/NCI-GDC/gdcdictionary.git"


def test_init_with_home() -> None:
    rm = repository.RepoMeta(remote_git_url=REMOTE_GIT_URL, name="smiths")
    assert rm.git_dir == f"{Path.home()}/.gml/git/smiths"


def test_init_repo_meta(tmpdir) -> None:

    with mock.patch.dict(os.environ, {"GML_GIT_HOME": f"{tmpdir}/.gml/git"}):
        rm = repository.RepoMeta(remote_git_url=REMOTE_GIT_URL, name="smiths")
        assert rm.git_dir == f"{tmpdir}/.gml/git/smiths"
        assert rm.is_cloned is False


def test_clone_repo() -> None:
    rm = repository.RepoMeta(remote_git_url=REMOTE_GIT_URL, name="smiths")
    r = repository.clone(rm)
    assert rm.is_cloned
    assert r.head()


def test_get_checkout_dir(tmpdir: Path) -> None:
    with mock.patch.dict(os.environ, {"GML_DICTIONARY_HOME": f"{tmpdir}/dictionaries"}):
        chk_dir = repository.get_checkout_dir(repo_name="smokes", commit_ref="sss")
        assert chk_dir == f"{tmpdir}/dictionaries/smokes/sss"


def test_get_commit_id() -> None:
    rm = repository.RepoMeta(remote_git_url=REMOTE_GIT_URL, name="smiths")
    repo = repository.clone(rm)

    commands = {
        b"f7ba557228bc113c92387c4eb6160621d27b53ef": repository.RepoCheckout(
            repo=rm, path="", commit="2.4.0"
        ),
        b"1595aef2484ab6fa6c945950b296c4031c2606fd": repository.RepoCheckout(
            repo=rm, path="", commit="2.3.0"
        ),
        b"7107e8116ce6ed8185626570dcba14b46e8e4d27": repository.RepoCheckout(
            repo=rm, path="", commit="release/avery", is_tag=False
        ),
    }
    for sha, command in commands.items():
        assert sha == repository.get_commit_id(repo, command.ref)


def test_checkout() -> None:
    repo = repository.RepoMeta(remote_git_url=REMOTE_GIT_URL, name="smiths")
    command = repository.RepoCheckout(
        repo=repo, path="gdcdictionary/schemas", commit="2.3.0", override=True
    )

    chk_dir = Path(repository.checkout(command))
    assert chk_dir.exists()

    entries = [f.name for f in chk_dir.iterdir()]
    assert "program.yaml" in entries
