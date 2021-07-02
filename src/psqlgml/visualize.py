import json

import yaml
from graphviz import Digraph


def visualize_json(file):
    with open(file) as fp:
        graph = json.load(fp)
        visualize_graph(graph)


def visualize_yaml(file):
    with open(file) as fp:
        graph = yaml.safe_load(fp)
        visualize_graph(graph)


def visualize_graph(graph):
    dot = Digraph("g", filename="btree.gv", node_attr={"shape": "record"})
    for node in graph["nodes"]:
        dot.node(node["submitter_id"])

    for edge in graph["edges"]:
        dot.edge(edge["src"], edge["dst"])
    dot.render()


if __name__ == "__main__":
    visualize_yaml(
        "/Users/qiaoqiao/PycharmProjects/graphmanager/tests/data/exports/versioning/gpas_sanger.yaml"
    )
