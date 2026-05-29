"""Integration-tier fixtures. Lives one level down so it only loads for this tier.

ro_engine is session-scope: connection setup is the expensive bit, and the role is
read-only so sharing across tests is safe. This is where fail-within-tier bites —
if pgvector :5433 is unreachable, the connection errors and the whole tier fails
loud (chosen over skip, so a broken env is never silently hidden)."""

import pytest
from sqlalchemy import text

from ingestion.db import get_readonly_engine


@pytest.fixture(scope="session")
def ro_engine():
    engine = get_readonly_engine()
    # touch the connection now so an unreachable :5433 fails loudly up front
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return engine
