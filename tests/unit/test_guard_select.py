"""_guard_select: belt-and-suspenders SQL gate (the real guarantee is the RO role).
Rejects multi-statement, non-SELECT/WITH, and write/DDL keywords. Pure function.

The keyword guard is intentionally conservative: it matches the word anywhere,
even inside a string literal. That's by design — false positives are acceptable
because the RO role is the actual safety boundary."""

import pytest

from agents.tools import _guard_select


# --- accepted ------------------------------------------------------------
def test_plain_select_returns_stripped():
    assert _guard_select("SELECT * FROM job_postings_aggregate") == (
        "SELECT * FROM job_postings_aggregate"
    )


def test_lowercase_select_ok():
    assert _guard_select("select 1") == "select 1"


def test_with_cte_ok():
    sql = "WITH t AS (SELECT 1 AS n) SELECT n FROM t"
    assert _guard_select(sql) == sql


def test_trailing_semicolon_stripped():
    assert _guard_select("SELECT 1;") == "SELECT 1"


# --- rejected ------------------------------------------------------------
def test_multi_statement_rejected():
    with pytest.raises(ValueError):
        _guard_select("SELECT 1; SELECT 2")


def test_non_select_rejected():
    with pytest.raises(ValueError):
        _guard_select("DELETE FROM job_postings_aggregate")


def test_update_rejected():
    with pytest.raises(ValueError):
        _guard_select("UPDATE job_postings_aggregate SET x = 1")


def test_write_keyword_inside_select_rejected():
    # conservative: 'drop' anywhere trips the guard, even in a string literal
    with pytest.raises(ValueError):
        _guard_select("SELECT * FROM t WHERE note = 'drop the bass'")
