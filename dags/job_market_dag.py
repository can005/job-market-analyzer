import os
from datetime import datetime

from airflow.decorators import dag, task

from core.config import AGGREGATE_CSV, RAW_DATA_DIR, SECTOR_CSV
from ingestion.clean import main as clean_main
from ingestion.load import main as load_main


@dag(
    dag_id="job_market_pipeline",
    schedule="@daily",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["job-market"],
)
def job_market_pipeline():

    @task
    def extract() -> None:
        for f in [AGGREGATE_CSV, SECTOR_CSV]:
            path = RAW_DATA_DIR + f
            if not os.path.exists(path):
                raise FileNotFoundError(f"Raw file not found: {path}")
        print("Raw files verified.")

    @task
    def clean() -> None:
        clean_main()

    @task
    def load() -> None:
        load_main()

    extract() >> clean() >> load()


job_market_pipeline()