from ftviz.db.utils import setup_database, load_family_tree
from ftviz.models import Node, FamilyTree


def main():
    engine = setup_database("sqlite:///data/ftviz.db")
    ft = load_family_tree(engine)

    ft.render(format="png")


if __name__ == "__main__":
    main()
