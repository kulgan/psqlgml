import logging
import os
from pathlib import Path

import attr
from dulwich import objects, porcelain

__all__ = [
    "checkout",
    "clone",
    "RepoMeta",
    "RepoCheckout",
]

logger = logging.getLogger(__name__)


@attr.s(auto_attribs=True, frozen=True)
class RepoMeta:
    name: str
    remote_git_url: str
    origin: bytes = b"origin"

    @property
    def git_dir(self) -> str:
        git_home = os.getenv("GML_GIT_HOME", f"{Path.home()}/.gml/git")
        dir_home = f"{git_home}/{self.name}"
        os.makedirs(dir_home, exist_ok=True)
        return dir_home

    @property
    def is_cloned(self) -> bool:
        return os.path.exists("{}/.git".format(self.git_dir))


@attr.s(auto_attribs=True)
class RepoCheckout:
    repo: RepoMeta
    commit: str
    path: str
    origin: bytes = b"origin"
    is_tag: bool = True
    override: bool = False

    @property
    def ref(self) -> str:
        if self.is_tag:
            return f"refs/tags/{self.commit}"
        return f"refs/remotes/{self.origin.decode()}/{self.commit}"


def get_checkout_dir(repo_name: str, commit_ref: str) -> str:
    dict_home = os.getenv("GML_DICTIONARY_HOME", f"{Path.home()}/.gml/dictionaries")
    chk = f"{dict_home}/{repo_name}/{commit_ref}"
    return chk


def get_commit_id(repo: porcelain.Repo, commit_ref: str) -> bytes:
    obj: objects.ShaFile = porcelain.parse_object(repo, commit_ref)
    if isinstance(obj, objects.Commit):
        return obj.id
    if isinstance(obj, objects.Tag):
        return obj.object[1]
    raise ValueError(f"Unrecognized commit {commit_ref}")


def clone(repo_meta: RepoMeta) -> porcelain.Repo:
    if not repo_meta.is_cloned:
        logger.debug(
            f"cloning new repository {repo_meta.remote_git_url} into {repo_meta.git_dir}"
        )

        porcelain.clone(
            repo_meta.remote_git_url,
            target=repo_meta.git_dir,
            depth=1,
            checkout=False,
            origin=repo_meta.origin,
        )
    return porcelain.Repo(repo_meta.git_dir)


def checkout(command: RepoCheckout) -> str:
    repo = clone(command.repo)
    commit_id = get_commit_id(repo, command.ref)
    chk_dir = get_checkout_dir(command.repo.name, command.commit)

    if os.path.exists(chk_dir) and not command.override:
        return chk_dir

    os.makedirs(chk_dir, exist_ok=True)
    commit_tree: objects.Tree = porcelain.get_object_by_path(
        repo, command.path, committish=commit_id
    )

    # dump schema files to dump location
    for entry in commit_tree.items():

        file_name = entry.path.decode()
        blob = repo.get_object(entry.sha)

        # skip sub folders
        if not isinstance(blob, objects.Blob):
            logger.debug(f"Skipping extra folders in schema directory {file_name}")
            continue

        with open(f"{chk_dir}/{file_name}", "wb") as f:
            f.write(blob.as_raw_string())
    return chk_dir
