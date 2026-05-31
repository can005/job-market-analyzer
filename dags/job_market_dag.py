from datetime import datetime, timedelta

from airflow.decorators import dag, task

from ingestion.market_clean import main as clean_main
from ingestion.market_fetch import main as fetch_main
from ingestion.market_load import main as load_main


@dag(
    dag_id="job_market_pipeline",
    schedule="@daily",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["job-market"],
)
def job_market_pipeline():

    @task(retries=3, retry_delay=timedelta(minutes=2))
    def extract() -> None:
        fetch_main()

    @task
    def clean() -> None:
        clean_main()

    @task
    def load() -> None:
        load_main()

    extract() >> clean() >> load()


job_market_pipeline()
