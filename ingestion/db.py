import os
from typing import Type

from dotenv import load_dotenv
from sqlalchemy import Engine, create_engine
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import DeclarativeBase, Session
from sqlalchemy.pool import QueuePool

from core.config import UPSERT_BATCH_SIZE
from core.validators import validate_db_env, validate_readonly_db_env

load_dotenv()

def bulk_upsert(session: Session,
                model: Type[DeclarativeBase], 
                records: list, 
                conflict_columns: list) -> None:
    for i in range(0, len(records), UPSERT_BATCH_SIZE):
        batch = records[i:i + UPSERT_BATCH_SIZE]
        stmt = insert(model).values(batch)
        stmt = stmt.on_conflict_do_nothing(index_elements=conflict_columns)
        session.execute(stmt)
        session.commit()
        print(f"{model.__tablename__}: batch {i // UPSERT_BATCH_SIZE + 1} ({len(batch)} rows)")


def get_engine() -> Engine:
    validate_db_env()
    url = (
        f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )
    return create_engine(
        url,
        poolclass=QueuePool,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_pre_ping=True,
    )

def get_readonly_engine() -> Engine:
    validate_readonly_db_env()
    url = (
        f"postgresql+psycopg2://{os.getenv('RO_DB_USER')}:{os.getenv('RO_DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )
    return create_engine(url, poolclass=QueuePool, pool_pre_ping=True)

def get_connection_string() -> str:
    validate_db_env()
    return (
        f"postgresql+psycopg://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )
