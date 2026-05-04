import os
from typing import Type

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import Engine, create_engine
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import DeclarativeBase, Session
from sqlalchemy.pool import QueuePool

from ingestion.config import AGGREGATE_CSV, CLEAN_DATA_DIR, SECTOR_CSV
from ingestion.models import Aggregate, Base, Sector

load_dotenv()


def validate_env() -> None:
    required = ['DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_PORT', 'DB_NAME']
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise EnvironmentError(f"Missing environment variables: {missing}")


def get_engine() -> Engine:
    validate_env()
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


BATCH_SIZE = 1000


def bulk_upsert(session: Session,
                model: Type[DeclarativeBase], 
                records: list, 
                conflict_columns: list) -> None:
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i:i + BATCH_SIZE]
        stmt = insert(model).values(batch)
        stmt = stmt.on_conflict_do_nothing(index_elements=conflict_columns)
        session.execute(stmt)
        session.commit()
        print(f"{model.__tablename__}: batch {i // BATCH_SIZE + 1} ({len(batch)} rows)")


def load_aggregate(session: Session, df) -> None:
    records = df.to_dict(orient='records')
    print(f"Loading {len(records)} rows into {Aggregate.__tablename__}")
    bulk_upsert(session, Aggregate, records, ['date', 'job_country', 'variable'])


def load_sector(session: Session, df) -> None:
    records = df.to_dict(orient='records')
    print(f"Loading {len(records)} rows into {Sector.__tablename__}")
    bulk_upsert(session, Sector, records, ['date', 'job_country', 'sector_name', 'variable'])


def main() -> None:
    print("Starting load...")
    try:
        engine = get_engine()
        Base.metadata.create_all(engine)
        print("Database tables verified")

        agg = pd.read_csv(CLEAN_DATA_DIR + AGGREGATE_CSV)
        sec = pd.read_csv(CLEAN_DATA_DIR + SECTOR_CSV)
        print("CSVs loaded")

        with Session(engine) as session:
            load_aggregate(session, agg)
            load_sector(session, sec)
            agg_count = session.query(Aggregate).count()
            sec_count = session.query(Sector).count()

        print(f"Done — Aggregate: {agg_count} | Sector: {sec_count}")

    except EnvironmentError as e:
        raise EnvironmentError(f"Configuration error: {e}")
    except Exception as e:
        raise Exception(f"Unexpected error: {e}")
    
if __name__ == '__main__':
    main()