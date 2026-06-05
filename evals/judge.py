"""Pluggable LLM judge for the scoring-eval reasoning-quality layer.

Provider/model read from `JUDGE_MODEL` (default `gpt-4o`). Key-gated:
`get_judge()` returns `None` when the relevant provider API key is missing, so
the caller can skip the judged metric and keep the deterministic floor running.
Provider clients are imported lazily so non-default providers don't require a
hard dependency."""

import os

DEFAULT_JUDGE_MODEL = "gpt-4o"


def _provider_for_model(model: str) -> str:
    if model.startswith("gpt-"):
        return "openai"
    if model.startswith("claude-"):
        return "anthropic"
    raise ValueError(f"Unsupported judge model: {model}")


def _api_key_env_var(provider: str) -> str:
    return {"openai": "OPENAI_API_KEY", "anthropic": "ANTHROPIC_API_KEY"}[provider]


def get_judge():
    model = os.getenv("JUDGE_MODEL", DEFAULT_JUDGE_MODEL)
    provider = _provider_for_model(model)
    if not os.getenv(_api_key_env_var(provider)):
        return None
    if provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=model, temperature=0)
    from langchain_anthropic import ChatAnthropic

    return ChatAnthropic(model=model, temperature=0)


def judge_metadata() -> dict:
    model = os.getenv("JUDGE_MODEL", DEFAULT_JUDGE_MODEL)
    return {"judge_model": model, "judge_provider": _provider_for_model(model)}
