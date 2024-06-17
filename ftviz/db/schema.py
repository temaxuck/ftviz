from sqlalchemy import (
    MetaData,
    Table,
    Column,
    Integer,
    String,
    Date,
    LargeBinary,
    ForeignKey,
)
from sqlalchemy.orm import registry, relationship

from ftviz.models import Node


# Naming Convention for tables and constraints
convention = {
    "all_column_names": lambda constraint, table: "_".join(
        [column.name for column in constraint.columns.values()]
    ),
    # index naming
    "ix": "ix__%(table_name)s_%(all_column_names)s",
    # unique index naming
    "uq": "uq__%(table_name)s_%(all_column_names)s",
    # check constraints naming
    "ck": "ck__%(table_name)s_%(constarint_name)s",
    # foreign key constraint naming
    "fk": "fk__%(table_name)s_%(all_column_names)s_%(referred_table_name)s",
    # primary key constraint naming
    "pk": "pk__%(table_name)s",
}

metadata = MetaData(naming_convention=convention)

mapper_registry = registry(metadata=metadata)

person_table = Table(
    "person",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String, nullable=False),
    Column("birth_date", Date, nullable=False),
    Column("death_date", Date, nullable=True),
    Column("image_path", String, nullable=True),
)

relation_table = Table(
    "relation",
    metadata,
    Column("parent_id", ForeignKey("person.id"), primary_key=True),
    Column("child_id", ForeignKey("person.id"), primary_key=True),
)

mapper_registry.map_imperatively(
    Node,
    person_table,
    properties={
        "children": relationship(
            Node,
            secondary=relation_table,
            primaryjoin=(relation_table.c.parent_id == person_table.c.id),
            secondaryjoin=(relation_table.c.child_id == person_table.c.id),
            backref="parent",
            lazy="joined",
        )
    },
)
