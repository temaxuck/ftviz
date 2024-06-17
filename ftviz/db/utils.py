from logging import getLogger
from sqlalchemy import Engine, create_engine, Connection, select
from sqlalchemy.exc import ArgumentError
from sqlalchemy.orm import sessionmaker, selectinload
from typing import List

from ftviz.db.schema import metadata, person_table
from ftviz.models import Node

SQLITE_URI = str

logger = getLogger(__name__)


def setup_database(database_uri: SQLITE_URI) -> Engine:
    logger.info(f"Connecting to database: {database_uri}")

    try:
        engine = create_engine(database_uri)
    except ArgumentError as e:
        logger.error(
            (
                f"Could not connect to database: {database_uri}\n"
                f"Due to following error:\n{e}"
            )
        )
        raise e

    metadata.create_all(engine)
    return engine


def get_all_nodes(engine: Engine) -> List[Node]:
    get_session = sessionmaker(bind=engine)
    with get_session() as session:
        nodes = (
            session.execute(select(Node).options(selectinload(Node.children)))
            .scalars()
            .all()
        )

    return nodes
