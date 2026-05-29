FROM apache/airflow:3.2.1

COPY requirements-base.txt requirements-ingestion.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements-base.txt -r /tmp/requirements-ingestion.txt