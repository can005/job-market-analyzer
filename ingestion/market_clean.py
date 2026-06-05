import logging

import pandas as pd

from core.config import CLEAN_DATA_DIR, MARKET_AGGREGATE_CSV, MARKET_SECTOR_CSV, RAW_DATA_DIR
from core.logging import setup_logging

logger = logging.getLogger(__name__)


def clean_aggregate(df: pd.DataFrame) -> pd.DataFrame:
    df["date"] = pd.to_datetime(df["date"])
    df.columns = ["date", "job_country", "index_sa", "index_nsa", "variable"]
    df = df.dropna()
    df = df.drop_duplicates(subset=["date", "job_country", "variable"])
    return df


def clean_sector(df: pd.DataFrame) -> pd.DataFrame:
    df["date"] = pd.to_datetime(df["date"])
    df.columns = ["date", "job_country", "index_value", "variable", "sector_name"]
    df = df.dropna()
    df = df.drop_duplicates(subset=["date", "job_country", "sector_name", "variable"])
    return df


def process_aggregate() -> None:
    logger.info("market_clean.aggregate.begin")

    df = pd.read_csv(RAW_DATA_DIR + MARKET_AGGREGATE_CSV)
    logger.info("market_clean.aggregate.raw", extra={"shape": list(df.shape)})

    df = clean_aggregate(df)
    logger.info("market_clean.aggregate.clean", extra={"shape": list(df.shape)})

    df.to_csv(CLEAN_DATA_DIR + MARKET_AGGREGATE_CSV, index=False)
    logger.info("market_clean.aggregate.done")


def process_sector() -> None:
    logger.info("market_clean.sector.begin")

    df = pd.read_csv(RAW_DATA_DIR + MARKET_SECTOR_CSV)
    logger.info("market_clean.sector.raw", extra={"shape": list(df.shape)})

    df = clean_sector(df)
    logger.info("market_clean.sector.clean", extra={"shape": list(df.shape)})

    df.to_csv(CLEAN_DATA_DIR + MARKET_SECTOR_CSV, index=False)
    logger.info("market_clean.sector.done")


def main() -> None:
    setup_logging()
    process_aggregate()
    process_sector()


if __name__ == "__main__":
    main()
