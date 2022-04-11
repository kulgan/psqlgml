import glob
import shutil
import sys
import threading
from pathlib import Path

import pkg_resources
import pytest
from _pytest.fixtures import SubRequest
from _pytest.legacypath import TempdirFactory
from dulwich import porcelain
from dulwich.server import DictBackend, TCPGitServer

import psqlgml
from tests.helpers import SchemaInfo


@pytest.fixture(scope="session")
def data_dir() -> str:
    return pkg_resources.resource_filename("tests", "data")


@pytest.fixture(scope="session")
def local_dictionary(data_dir: str) -> psqlgml.Dictionary:
    return psqlgml.load_local(version="0.1.0", name="dictionary", dictionary_location=data_dir)


@pytest.fixture()
def local_schema(local_dictionary: psqlgml.Dictionary, tmpdir: Path) -> SchemaInfo:
    psqlgml.generate(loaded_dictionary=local_dictionary, output_location=str(tmpdir))
    return SchemaInfo(
        version=local_dictionary.version, name=local_dictionary.name, source_dir=str(tmpdir)
    )


@pytest.fixture()
def test_schema(local_schema: SchemaInfo) -> psqlgml.GmlSchema:
    return psqlgml.read_schema(
        name=local_schema.name,
        version=local_schema.version,
        schema_location=local_schema.source_dir,
    )


@pytest.fixture(scope="session")
def git_server(request: SubRequest, tmpdir_factory: TempdirFactory, data_dir: str):

    base_dir = f"{tmpdir_factory.mktemp('gitdata')}/rsvr"

    # copy dictionary files to tmp dir
    shutil.copytree(f"{data_dir}/dictionary/0.1.0", f"{base_dir}/gdcdictionary/schemas")

    # make a git repo for tests
    repo = porcelain.Repo.init(base_dir)

    # stage & commit dictionary files
    paths = [p.replace(f"{base_dir}/", "") for p in glob.glob(f"{base_dir}/**", recursive=True)]
    repo.stage(paths)
    print(",".join([f.decode(sys.getfilesystemencoding()) for f in repo.open_index()]))
    commit = repo.do_commit(b"Add items", committer=b"pytest <pytest@psqlgml.com>")

    # add tag and master branch
    assert repo.head() == commit
    repo.refs[b"refs/heads/master"] = commit
    repo.refs[b"refs/tags/0.1.0"] = commit

    print("================ refs ====================")
    print(repo.refs)

    # create remote repo
    backend = DictBackend({b"/rsvr": repo})
    dul_server = TCPGitServer(backend, b"localhost", 0)
    threading.Thread(target=dul_server.serve).start()

    server_addr, server_port = dul_server.socket.getsockname()
    request.addfinalizer(dul_server.shutdown)
    return f"git://{server_addr}:{server_port}/rsvr"
