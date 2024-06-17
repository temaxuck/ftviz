from ftviz.db.utils import setup_database, get_all_nodes
from ftviz.db.schema import relation_table
from ftviz.models import Node, FamilyTree


def main():
    ft = FamilyTree()
    engine = setup_database("sqlite:///data/ftviz.db")
    nodes = get_all_nodes(engine)

    for node in nodes:
        ft.add_node(node)
        for child in node.children:
            ft.add_edge(node, child)

    ft.render()


if __name__ == "__main__":
    main()
