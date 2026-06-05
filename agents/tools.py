import logging
import re

from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from sqlalchemy import text

from ingestion.db import get_readonly_engine
from ingestion.rag import get_vectorstore

logger = logging.getLogger(__name__)

# --- Indeed SQL guard ----------------------------------------------------
# The REAL guarantee is the read-only DB role (RO_DB_USER has no write grants).
ROW_CAP = 50
_WRITE_KEYWORDS = re.compile(
    r"\b(insert|update|delete|drop|alter|create|truncate|grant|revoke|copy|"
    r"merge|call|do|vacuum|comment|reindex|cluster)\b",
    re.IGNORECASE,
)


def collect_tool_output(result: dict) -> str:
    return "\n\n".join(m.content for m in result["messages"] if isinstance(m, ToolMessage))


def _guard_select(sql: str) -> str:
    stripped = sql.strip().rstrip(";").strip()
    if ";" in stripped:
        raise ValueError("Only a single statement is allowed (no ';' chaining).")
    if not stripped.lower().startswith(("select", "with")):
        raise ValueError("Only SELECT/WITH (read-only) queries are allowed.")
    if _WRITE_KEYWORDS.search(stripped):
        raise ValueError("Query contains a write/DDL keyword; read-only only.")
    return stripped


@tool
def query_job_postings(sql: str) -> str:
    """Run a READ-ONLY SQL query against the Indeed job-posting index tables and
    return rows as text. These are TIME SERIES of posting-index values (per
    country/sector/variable), NOT individual job listings.

    Tables and columns:
      job_postings_aggregate(date, job_country, index_sa, index_nsa, variable)
      job_postings_by_sector(date, job_country, index_value, variable, sector_name)

    Only a single SELECT/WITH statement is permitted. Results are capped at 50 rows.
    """
    safe = _guard_select(sql)
    engine = get_readonly_engine()
    with engine.connect() as conn:
        result = conn.execute(text(safe))
        rows = result.fetchmany(ROW_CAP)
        cols = list(result.keys())
    logger.info("tools.query_job_postings", extra={"sql": safe, "rows": len(rows)})
    if not rows:
        return "No rows returned."
    header = " | ".join(cols)
    body = "\n".join(" | ".join(str(v) for v in row) for row in rows)
    return f"{header}\n{body}"


@tool
def search_hn_job_postings(query: str, k: int = 25) -> str:
    """Semantic search over Hacker News 'Who is hiring' job postings. Returns the
    top-k matching postings as full text, each prefixed with its HN id.

    The HN id (e.g. `47975574`) is the posting's stable external identifier on
    Hacker News — use it when referring to a posting. Each posting's full text
    (company, role, salary, stack) is the searchable body.
    """
    vectorstore = get_vectorstore()
    docs = vectorstore.similarity_search(query, k=k)
    logger.info("tools.search_hn_job_postings", extra={"query": query, "k": k, "hits": len(docs)})
    if not docs:
        return "No matching postings found."
    blocks = [f"[id: {doc.metadata['id']}]\n{doc.page_content}" for doc in docs]
    return "\n\n".join(blocks)


@tool
def list_market_dimensions() -> str:
    """List the valid filter values for the Indeed market tables: the available
    'variable' values, job countries, and sector names. Call this BEFORE
    query_job_postings so WHERE filters use real values, not guesses."""
    engine = get_readonly_engine()
    with engine.connect() as conn:
        variables = [
            r[0] for r in conn.execute(text("SELECT DISTINCT variable FROM job_postings_aggregate"))
        ]
        countries = [
            r[0]
            for r in conn.execute(text("SELECT DISTINCT job_country FROM job_postings_aggregate"))
        ]
        sectors = [
            r[0]
            for r in conn.execute(
                text("SELECT DISTINCT sector_name FROM job_postings_by_sector ORDER BY sector_name")
            )
        ]
    logger.info(
        "tools.list_market_dimensions",
        extra={
            "variables": len(variables),
            "countries": len(countries),
            "sectors": len(sectors),
        },
    )
    return f"variables: {variables}\ncountries: {countries}\nsectors: {sectors}"
