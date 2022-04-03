import pytest

import psqlgml

pytestmark = [pytest.mark.slow, pytest.mark.dictionary]
REMOTE_GIT_URL = "https://github.com/NCI-GDC/gdcdictionary.git"


def test_remote_dictionary(remote_dictionary: psqlgml.Dictionary) -> None:
    assert len(remote_dictionary.links) == 92
    assert len(remote_dictionary.all_associations()) == 360

    assert {"diagnosis", "project"}.issubset(
        {link.dst for link in remote_dictionary.associations("case")}
    )
    assert {"analyte", "annotation", "file"}.issubset(
        {link.dst for link in remote_dictionary.associations("aliquot")}
    )


@pytest.mark.usefixtures("remote_dictionary")
def test_dictionary_loading() -> None:
    d1 = psqlgml.load_local(version="2.3.0", name="gdcdictionary")
    assert d1.schema
    assert len(d1.schema) == 81
    program = d1.schema["program"]

    assert program.id == "program"
    assert program.category == "administrative"
    assert program.downloadable is False
    assert program.required
