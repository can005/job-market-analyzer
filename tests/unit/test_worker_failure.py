"""Typed error policy for the workers.

Policy (see core/errors.py): workers catch only enumerated transient LLM errors
(timeout, rate-limit, transient API error) and degrade to "failed" + record the
reason. Anything else — KeyError, RuntimeError, ValidationError — propagates so
real bugs are not swallowed.

These are unit tests: the exceptions come from stubs, no LLM is called."""

import httpx
import openai
import pytest

import agents.market as market_mod
import agents.roles as roles_mod
from agents.supervisor import MARKET, ROLES


def _raise(exc: BaseException):
    def _inner(*args, **kwargs):
        raise exc

    return _inner


def _rate_limit_error() -> openai.RateLimitError:
    response = httpx.Response(status_code=429, request=httpx.Request("POST", "https://x"))
    return openai.RateLimitError("rate limited", response=response, body=None)


# --- transient errors degrade to "failed" + record reason ---------------------


def test_roles_node_records_reason_on_transient(monkeypatch):
    monkeypatch.setattr(roles_mod, "_find", _raise(_rate_limit_error()))
    out = roles_mod.roles_node({"profile": {"skills": [], "domain": "d", "logistics": "l"}})
    assert out == {
        "worker_status": {ROLES: "failed"},
        "worker_errors": {ROLES: "RateLimitError"},
    }


def test_market_node_records_reason_on_transient(monkeypatch):
    monkeypatch.setattr(market_mod, "_gather", _raise(_rate_limit_error()))
    out = market_mod.market_node({"question": "any trend question"})
    assert out == {
        "worker_status": {MARKET: "failed"},
        "worker_errors": {MARKET: "RateLimitError"},
    }


# --- non-transient errors propagate (bugs must not be hidden) -----------------


def test_roles_node_propagates_runtime_error(monkeypatch):
    monkeypatch.setattr(roles_mod, "_find", _raise(RuntimeError("bug")))
    with pytest.raises(RuntimeError, match="bug"):
        roles_mod.roles_node({"profile": {"skills": [], "domain": "d", "logistics": "l"}})


def test_market_node_propagates_key_error(monkeypatch):
    monkeypatch.setattr(market_mod, "_gather", _raise(KeyError("missing")))
    with pytest.raises(KeyError):
        market_mod.market_node({"question": "any trend question"})
