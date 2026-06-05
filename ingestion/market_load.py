import logging

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from core.config import CLEAN_DATA_DIR, MARKET_AGGREGATE_CSV, MARKET_SECTOR_CSV
from core.logging import setup_logging
from ingestion.db import bulk_upsert, get_engine
from ingestion.models import Aggregate, Base, Sector

logger = logging.getLogger(__name__)


def load_aggregate(session: Session, df) -> None:
    records = df.to_dict(orient="records")
    logger.info(
        "market_load.aggregate.loading",
        extra={"rows": len(records), "table": Aggregate.__tablename__},
    )
    bulk_upsert(session, Aggregate, records, ["date", "job_country", "variable"])


def load_sector(session: Session, df) -> None:
    records = df.to_dict(orient="records")
    logger.info(
        "market_load.sector.loading",
        extra={"rows": len(records), "table": Sector.__tablename__},
    )
    bulk_upsert(session, Sector, records, ["date", "job_country", "sector_name", "variable"])


def main() -> None:
    setup_logging()
    logger.info("market_load.start")
    try:
        load_dotenv()
        engine = get_engine()
        Base.metadata.create_all(engine)
        logger.info("market_load.tables_verified")

        agg = pd.read_csv(CLEAN_DATA_DIR + MARKET_AGGREGATE_CSV)
        sec = pd.read_csv(CLEAN_DATA_DIR + MARKET_SECTOR_CSV)
        logger.info("market_load.csvs_loaded")

        with Session(engine) as session:
            load_aggregate(session, agg)
            load_sector(session, sec)
            agg_count = session.query(Aggregate).count()
            sec_count = session.query(Sector).count()

        logger.info(
            "market_load.done",
            extra={"aggregate_count": agg_count, "sector_count": sec_count},
        )

    except EnvironmentError as e:
        raise EnvironmentError(f"Configuration error: {e}")
    except Exception as e:
        raise Exception(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
