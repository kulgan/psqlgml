import logging
import os
import uuid
from functools import lru_cache

from graphviz import Digraph

import psqlgml.types
from psqlgml import resources

__all__ = ["draw"]

logger = logging.getLogger(__name__)


def draw(
    data_dir: str,
    data_file: str,
    output_dir: str,
    output_format: psqlgml.types.RenderFormat = "png",
    show_rendered: bool = False,
) -> None:
    graph = resources.load_resource(data_dir, data_file)

    output_name = data_file.split(".")[0]
    unique_field: psqlgml.types.UniqueFieldType = graph.get("unique_field", "submitter_id")
    dot = Digraph("g", filename=f"{output_name}.gv", node_attr={"shape": "record"})
    for node in graph["nodes"]:
        dot.node(node[unique_field], fillcolor=get_color(node["label"]), style="filled")

    for edge in graph["edges"]:
        dot.edge(edge["src"], edge["dst"])
    dot.render(view=show_rendered, directory=output_dir, format=output_format)


@lru_cache(maxsize=256)
def get_color(label: str) -> str:
    label = str(uuid.uuid5(UUID_NAMESPACE, label))
    label_color = hex(int("".join(map(str, map(ord, label)))) & 0x00FFFFFF)
    return "#{:f<6}".format(label_color[2:])


UUID_NAMESPACE_SEED = os.getenv("UUID_NAMESPACE_SEED", "f0d2633b-cd8b-45ca-ae86-1d5c759ba0d1")
UUID_NAMESPACE = uuid.UUID("urn:uuid:{}".format(UUID_NAMESPACE_SEED), version=4)
