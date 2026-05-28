# Job Market Analyzer

An end-to-end AI engineering project that combines labor market data pipelines, RAG, multi-agent systems, and observability.

## Architecture
- **Phase 1** — Data pipeline: ingestion, cleaning, PostgreSQL storage, Airflow orchestration
- **Phase 2** — RAG system over real job postings with semantic search and evaluation
- **Phase 3** — Multi-agent system: supervisor-routed workers for market-trend analysis, role finding, and match scoring (cover-letter writer planned)
- **Phase 4** — Observability with LangSmith tracing and a Streamlit dashboard

## Data Sources
- [Indeed Hiring Lab](https://github.com/hiring-lab/job_postings_tracker) (Creative Commons 4.0)
- Hacker News "Who is Hiring" public API

## Tech Stack
Python · PostgreSQL · pgvector · Airflow · LangChain · LangGraph · OpenAI · LangSmith · Streamlit · Docker

## Status
- ✅ **Phase 1 — Data pipeline** — complete. Indeed Hiring Lab and Hacker News ingestion, cleaning, and PostgreSQL/pgvector storage, orchestrated by two Airflow DAGs (daily market pipeline, monthly HN pipeline) on a Dockerised stack.
- ✅ **Phase 2 — RAG** — complete. pgvector retrieval over HN job postings, with a RAGAS evaluation harness covering faithfulness, context precision/recall, and answer relevancy.
- 🚧 **Phase 3 — Multi-agent system** — in progress. A LangGraph supervisor routes an intent classifier to a market-trends worker (read-only SQL over the Indeed index) and a roles worker (semantic HN search plus weighted match scoring). Cover-letter writer not yet built.
- 🚧 **Phase 4 — Observability** — in progress. LangSmith tracing is wired into the agent graph; the Streamlit dashboard is not yet built.

## How to Run
_Coming soon_

## Author
Carlos Novo — [LinkedIn](https://linkedin.com/in/carlosnovo-2)