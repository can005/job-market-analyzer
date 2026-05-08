import pandas as pd
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from ingestion.config import AGGREGATE_CSV, CLEAN_DATA_DIR, SECTOR_CSV
from ingestion.db import bulk_upsert, get_engine
from ingestion.models import Aggregate, Base, Sector

load_dotenv()

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