from pathlib import Path

import pytest
from PIL import Image

import psqlgml.types
from psqlgml import visualization


@pytest.mark.parametrize("render_format", ["png", "jpeg", "pdf"])
@pytest.mark.parametrize("data_file", ["simple_valid.json", "simple_valid.yaml"])
def test_draw(
    data_dir: str, tmpdir: Path, data_file: str, render_format: psqlgml.types.RenderFormat
) -> None:
    output_dir = f"{tmpdir}"
    visualization.draw(data_dir, data_file, output_dir, output_format=render_format)

    dot_output = Path(f"{tmpdir}/simple_valid.gv.{render_format}")
    assert dot_output.exists()

    if render_format == "pdf":
        return

    img = Image.open(dot_output)
    assert img.format.lower() == render_format


@pytest.mark.parametrize(
    "label, color",
    [
        ("case", "#ce652b"),
        ("program", "#a75607"),
        ("aligned_reads", "#a6028d"),
        ("puppy", "#96bb93"),
    ],
)
def test_get_color(label: str, color: str):
    assert color == visualization.get_color(label)
