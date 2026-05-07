from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator

from ingestion.clean import main as clean_main
from ingestion.load import main as load_main


def extract() -> None:
    import os

    from ingestion.config import AGGREGATE_CSV, RAW_DATA_DIR, SECTOR_CSV
    for f in [AGGREGATE_CSV, SECTOR_CSV]:
        path = RAW_DATA_DIR + f
        if not os.path.exists(path):
            raise FileNotFoundError(f"Raw file not found: {path}")
    print("Raw files verified.")


with DAG(
    dag_id="job_market_pipeline",
    schedule="@daily",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["job-market"],
) as dag:

    t1 = PythonOperator(task_id="extract", python_callable=extract)
    t2 = PythonOperator(task_id="clean", python_callable=clean_main)
    t3 = PythonOperator(task_id="load", python_callable=load_main)

    t1 >> t2 >> t3