"""Seed minimal data into pgvector so the integration tests have something to read.

Idempotent (ON CONFLICT DO NOTHING) — safe to re-run. Reads DB env via the
standard ingestion.db connection helpers. Used by the CI integration job
before pytest -m integration."""

from datetime import datetime

from dotenv import load_dotenv
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from ingestion.db import get_engine
from ingestion.models import Aggregate, Base, Sector

AGGREGATE_ROWS = [
    {
        "date": datetime(2025, 1, 1),
        "job_country": "US",
        "index_sa": 100.0,
        "index_nsa": 98.5,
        "variable": "new postings",
    },
    {
        "date": datetime(2025, 2, 1),
        "job_country": "US",
        "index_sa": 102.3,
        "index_nsa": 101.0,
        "variable": "new postings",
    },
    {
        "date": datetime(2025, 1, 1),
        "job_country": "US",
        "index_sa": 110.0,
        "index_nsa": 109.0,
        "variable": "total postings",
    },
]

SECTOR_ROWS = [
    {
        "date": datetime(2025, 1, 1),
        "job_country": "US",
        "index_value": 105.0,
        "variable": "new postings",
        "sector_name": "Software Development",
    },
    {
        "date": datetime(2025, 1, 1),
        "job_country": "US",
        "index_value": 95.0,
        "variable": "new postings",
        "sector_name": "Finance",
    },
    {
        "date": datetime(2025, 1, 1),
        "job_country": "US",
        "index_value": 88.0,
        "variable": "new postings",
        "sector_name": "Healthcare",
    },
]


def _upsert(session: Session, model, rows: list[dict], conflict_columns: list[str]) -> None:
    stmt = insert(model).values(rows).on_conflict_do_nothing(index_elements=conflict_columns)
    session.execute(stmt)
    session.commit()


def main() -> None:
    load_dotenv()
    engine = get_engine()
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        _upsert(session, Aggregate, AGGREGATE_ROWS, ["date", "job_country", "variable"])
        _upsert(
            session, Sector, SECTOR_ROWS, ["date", "job_country", "sector_name", "variable"]
        )


if __name__ == "__main__":
    main()
