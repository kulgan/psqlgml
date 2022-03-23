import os
from pathlib import Path
from unittest import mock

from psqlgml.dictionaries import repo

REMOTE_GIT_URL = "https://github.com/NCI-GDC/gdcdictionary.git"


def test_init_with_home() -> None:
    rm = repo.RepoMeta(remote_git_url=REMOTE_GIT_URL, name="smiths")
    assert rm.git_dir == f"{Path.home()}/.gml/git/smiths"


def test_init_repo_meta(tmpdir) -> None:

    with mock.patch.dict(os.environ, {"GML_GIT_HOME": f"{tmpdir}/.gml/git"}):
        rm = repo.RepoMeta(remote_git_url=REMOTE_GIT_URL, name="smiths")
        assert rm.git_dir == f"{tmpdir}/.gml/git/smiths"
        assert rm.is_cloned is False


def test_clone_repo() -> None:
    rm = repo.RepoMeta(remote_git_url=REMOTE_GIT_URL, name="smiths")
    r = repo.clone(rm)
    assert rm.is_cloned
    assert r.head()


def test_get_checkout_dir(tmpdir: Path) -> None:
    with mock.patch.dict(os.environ, {"GML_DICTIONARY_HOME": f"{tmpdir}/dictionaries"}):
        chk_dir = repo.get_checkout_dir(repo_name="smokes", commit_ref="sss")
        assert chk_dir == f"{tmpdir}/dictionaries/smokes/sss"


def test_get_commit_id() -> None:
    rm = repo.RepoMeta(remote_git_url=REMOTE_GIT_URL, name="smiths")
    project = repo.clone(rm)

    commands = {
        b"f7ba557228bc113c92387c4eb6160621d27b53ef": repo.RepoCheckout(
            repo=rm, path="", commit="2.4.0"
        ),
        b"1595aef2484ab6fa6c945950b296c4031c2606fd": repo.RepoCheckout(
            repo=rm, path="", commit="2.3.0"
        ),
        b"7107e8116ce6ed8185626570dcba14b46e8e4d27": repo.RepoCheckout(
            repo=rm, path="", commit="release/avery", is_tag=False
        ),
    }
    for sha, command in commands.items():
        assert sha == repo.get_commit_id(project, command.ref)


def test_checkout() -> None:
    project = repo.RepoMeta(remote_git_url=REMOTE_GIT_URL, name="smiths")
    command = repo.RepoCheckout(
        repo=project, path="gdcdictionary/schemas", commit="2.3.0", override=True
    )

    chk_dir = Path(repo.checkout(command))
    assert chk_dir.exists()

    entries = [f.name for f in chk_dir.iterdir()]
    assert "program.yaml" in entries
