from datetime import datetime

from airflow.decorators import dag, task

from ingestion.hn_embed import embed_postings
from ingestion.hn_fetch import main as hn_fetch_main


@dag(
    dag_id="hn_pipeline",
    schedule="0 0 1 * *",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["hn", "embeddings"],
)
def hn_pipeline():

    @task
    def fetch() -> None:
        hn_fetch_main()

    @task
    def embed() -> None:
        embed_postings()

    fetch() >> embed()


hn_pipeline()
