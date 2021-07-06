import logging

from graphviz import Digraph

from psqlgml import resources

logger = logging.getLogger(__name__)


def visualize_graph(data_dir: str, data_file: str, output_dir: str) -> None:
    graph = resources.merge(data_dir, data_file)

    output_name = data_file.split(".")[0]
    dot = Digraph("g", filename=f"{output_dir}/{output_name}.gv", node_attr={"shape": "record"})
    for node in graph["nodes"]:
        dot.node(node["submitter_id"], label=node["label"])

    for edge in graph["edges"]:
        dot.edge(edge["src"], edge["dst"])
    dot.render(view=True)


if __name__ == "__main__":
    sample = "versioning/gpas_rna_seq.yaml"
    rss_dir = "/home/rogwara/git/graphmanager/tests/data/exports"
