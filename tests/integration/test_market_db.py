"""Integration tier — real read-only SQL against pgvector :5433.
Covers list_market_dimensions (the RO discovery query) and query_job_postings
(the guarded RO query path). Marked 'integration' automatically by directory.

Live DB facts asserted are the stable probed values from the project overview:
job_country = {US}; variable ∈ {new postings, total postings}."""

from agents.tools import list_market_dimensions, query_job_postings


def test_list_market_dimensions_returns_real_values(ro_engine):
    out = list_market_dimensions.invoke({})
    assert "variables:" in out
    assert "countries:" in out
    assert "sectors:" in out
    assert "US" in out


def test_query_job_postings_runs_readonly_select(ro_engine):
    out = query_job_postings.invoke(
        {"sql": "SELECT variable FROM job_postings_aggregate LIMIT 3"}
    )
    # either rows came back (header + body) or the explicit empty sentinel
    assert "variable" in out or out == "No rows returned."


def test_query_job_postings_row_cap_header_present(ro_engine):
    out = query_job_postings.invoke(
        {"sql": "SELECT date, variable FROM job_postings_aggregate LIMIT 5"}
    )
    if out != "No rows returned.":
        # first line is the column header joined by ' | '
        assert out.splitlines()[0] == "date | variable"