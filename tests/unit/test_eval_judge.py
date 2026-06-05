"""Judge-factory tests. Provider branching by env; key-gating returns None."""

import pytest

from evals.judge import DEFAULT_JUDGE_MODEL, get_judge, judge_metadata


def test_default_judge_is_openai_when_key_present(monkeypatch):
    monkeypatch.delenv("JUDGE_MODEL", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    judge = get_judge()
    assert judge is not None
    assert type(judge).__name__ == "ChatOpenAI"


def test_returns_none_when_openai_key_missing(monkeypatch):
    monkeypatch.delenv("JUDGE_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert get_judge() is None


def test_unsupported_model_raises(monkeypatch):
    monkeypatch.setenv("JUDGE_MODEL", "mistral-large")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    with pytest.raises(ValueError, match="Unsupported judge model"):
        get_judge()


def test_judge_metadata_reports_model_and_provider(monkeypatch):
    monkeypatch.delenv("JUDGE_MODEL", raising=False)
    meta = judge_metadata()
    assert meta == {"judge_model": DEFAULT_JUDGE_MODEL, "judge_provider": "openai"}

    monkeypatch.setenv("JUDGE_MODEL", "claude-3-5-sonnet-latest")
    meta = judge_metadata()
    assert meta == {"judge_model": "claude-3-5-sonnet-latest", "judge_provider": "anthropic"}
