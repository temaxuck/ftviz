import graphviz
import os

from datetime import date
from typing import Optional, List


class Node:
    def __repr__(self):
        return (
            f"{self.name} "
            f"({self.birth_date.year} - {self.death_date.year if self.death_date else 'Present'})"
        )


class FamilyTree:
    def __init__(self):
        self.root = graphviz.Digraph(engine="dot", comment="Family Tree")
        self.nodes = []

    @classmethod
    def label_format(
        cls,
        name: str,
        img: os.PathLike,
        birth_date: date,
        death_date: Optional[date],
    ) -> str:
        return (
            "<"
            '<TABLE CELLSPACING="2" CELLPADDING="2" BORDER="0">'
            f'<TR><TD><IMG SRC="{img}" /></TD></TR>'
            f"<TR><TD><B>{name}</B></TD></TR>"
            f"<TR><TD><I>{birth_date.year} -"
            f"{death_date.year if death_date else 'Present'}</I></TD></TR>"
            "</TABLE>"
            ">"
        )

    def add_node(
        self,
        node: Node,
    ):
        self.nodes.append(node)
        label = self.label_format(
            node.name, node.image_path, node.birth_date, node.death_date
        )
        self.root.node(
            str(node.id),
            shape="plaintext",
            label=label,
        )

    def add_edge(self, parent: Node, child: Node):
        self.root.edge(str(parent.id), str(child.id))

    def render(self, path: os.PathLike = "output/family-tree.gv", format="pdf"):
        self.root.render(path, format=format)
