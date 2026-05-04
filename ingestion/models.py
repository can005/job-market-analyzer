from ingestion.config import AGGREGATE_TABLE_NAME, SECTOR_TABLE_NAME
from sqlalchemy import Column, Integer, Float, String, DateTime, UniqueConstraint
from sqlalchemy.orm import declarative_base
from datetime import datetime, timezone



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

