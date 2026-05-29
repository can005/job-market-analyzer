"""Two deliberately separate sets:

- model-invalid  → raw dicts that fail Pydantic Profile *construction*.
- business-rule-invalid → structurally valid Profiles that validate_profile rejects
  (empty skills, duplicate skill, out-of-range years, empty domain/logistics).

Year bounds come from config (MIN_YEARS / MAX_YEARS) — referenced, never hardcoded,
so test and validator share one source of truth.
"""

import pytest
from pydantic import ValidationError

from core.config import MAX_YEARS, MIN_YEARS
from core.schemas import Profile, ProfileSkill
from core.validators import validate_profile


def _profile_dict(skills=None, domain="backend", logistics="remote"):
    """Build via the model, then dump — never hand-write the dict."""
    skills = skills if skills is not None else [ProfileSkill(skill="C++", years=10)]
    return Profile(skills=skills, domain=domain, logistics=logistics).model_dump()


# --- happy path ----------------------------------------------------------
def test_valid_profile_passes():
    validate_profile(_profile_dict())  # no raise


def test_year_bounds_inclusive():
    validate_profile(_profile_dict(skills=[ProfileSkill(skill="C++", years=MIN_YEARS)]))
    validate_profile(_profile_dict(skills=[ProfileSkill(skill="C++", years=MAX_YEARS)]))


# --- business-rule-invalid (valid Pydantic, rejected by validator) -------
def test_not_a_dict_rejected():
    with pytest.raises(ValueError):
        validate_profile(["not", "a", "dict"])


def test_empty_skills_rejected():
    with pytest.raises(ValueError):
        validate_profile(_profile_dict(skills=[]))


def test_empty_domain_rejected():
    with pytest.raises(ValueError):
        validate_profile(_profile_dict(domain=""))


def test_empty_logistics_rejected():
    with pytest.raises(ValueError):
        validate_profile(_profile_dict(logistics=""))


def test_duplicate_skill_rejected():
    dup = [ProfileSkill(skill="C++", years=10), ProfileSkill(skill="c++", years=3)]
    with pytest.raises(ValueError):
        validate_profile(_profile_dict(skills=dup))


def test_years_above_max_rejected():
    over = [ProfileSkill(skill="C++", years=MAX_YEARS + 1)]
    with pytest.raises(ValueError):
        validate_profile(_profile_dict(skills=over))


def test_years_below_min_rejected():
    under = [ProfileSkill(skill="C++", years=MIN_YEARS - 1)]
    with pytest.raises(ValueError):
        validate_profile(_profile_dict(skills=under))


# --- model-invalid (raw dict fails Pydantic construction) ----------------
def test_years_not_int_fails_construction():
    with pytest.raises(ValidationError):
        Profile(skills=[{"skill": "C++", "years": "five"}], domain="d", logistics="l")


def test_missing_skill_field_fails_construction():
    with pytest.raises(ValidationError):
        Profile(skills=[{"years": 5}], domain="d", logistics="l")


def test_missing_domain_fails_construction():
    with pytest.raises(ValidationError):
        Profile(skills=[{"skill": "C++", "years": 5}], logistics="l")
