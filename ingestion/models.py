from datetime import datetime, timezone

from pgvector.sqlalchemy import Vector
from sqlalchemy import BigInteger, Column, DateTime, Float, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import declarative_base

from ingestion.config import AGGREGATE_TABLE_NAME, HN_JOB_POSTING_TABLE_NAME, SECTOR_TABLE_NAME

Base = declarative_base()


class Aggregate(Base):
    __tablename__ = AGGREGATE_TABLE_NAME
    id          = Column(Integer, primary_key=True, autoincrement=True)
    date        = Column(DateTime)
    job_country = Column(String)
    index_sa    = Column(Float)
    index_nsa   = Column(Float)
    variable    = Column(String)
    ingested_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    __table_args__ = (
        UniqueConstraint('date', 'job_country', 'variable'),
    )


class Sector(Base):
    __tablename__ = SECTOR_TABLE_NAME
    id          = Column(Integer, primary_key=True, autoincrement=True)
    date        = Column(DateTime)
    job_country = Column(String)
    index_value = Column(Float)
    variable    = Column(String)
    sector_name = Column(String)
    ingested_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    __table_args__ = (
        UniqueConstraint('date', 'job_country', 'sector_name', 'variable'),
    )

class HNJobPosting(Base):
    __tablename__ = HN_JOB_POSTING_TABLE_NAME
    id            = Column(Integer, primary_key=True, autoincrement=True)
    thread_id     = Column(BigInteger)
    author        = Column(String)
    text          = Column(Text)
    created_at    = Column(DateTime)
    embedding     = Column(Vector(1536))
