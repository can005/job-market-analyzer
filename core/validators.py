import os

from core.config import PROFILE_FIELDS, MIN_YEARS, MAX_YEARS


def validate_db_env() -> None:
    required = [
        "DB_USER",
        "DB_PASSWORD",
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
    ]
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise EnvironmentError(f"Missing environment variables: {missing}")


def validate_readonly_db_env() -> None:
    required = ["RO_DB_USER", "RO_DB_PASSWORD", "DB_HOST", "DB_PORT", "DB_NAME"]
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise EnvironmentError(f"Missing environment variables: {missing}")


def validate_openai_llm_env() -> None:
    required = ["OPENAI_API_KEY"]
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise EnvironmentError(f"Missing environment variables: {missing}")


def validate_profile(profile: dict) -> None:
    if not isinstance(profile, dict):
        raise ValueError(f"profile must be a dict, got {type(profile).__name__}")
    missing = [f for f in PROFILE_FIELDS if not profile.get(f)]
    if missing:
        raise ValueError(f"profile missing required fields: {missing}")

    names = [entry["skill"].strip().lower() for entry in profile["skills"]]
    seen, duplicates = set(), []
    for name in names:
        if name in seen:
            duplicates.append(name)
        seen.add(name)
    if duplicates:
        raise ValueError(f"profile has duplicate skills: {duplicates}")

    out_of_range = [
        entry["skill"]
        for entry in profile["skills"]
        if entry["years"] < MIN_YEARS or entry["years"] > MAX_YEARS
    ]
    if out_of_range:
        raise ValueError(
            f"profile skills with years outside [{MIN_YEARS}, {MAX_YEARS}]: {out_of_range}"
        )

def validate_langsmith_env() -> None:
    required = [
        "LANGSMITH_TRACING",
        "LANGSMITH_API_KEY",
        "LANGSMITH_PROJECT",
    ]
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise EnvironmentError(f"Missing environment variables: {missing}")
