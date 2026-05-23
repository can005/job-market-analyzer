import os

from core.config import PROFILE_FIELDS


def validate_db_env() -> None:
    required = [
        'DB_USER', 
        'DB_PASSWORD', 
        'DB_HOST', 
        'DB_PORT', 
        'DB_NAME', 
        ]
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise EnvironmentError(f"Missing environment variables: {missing}")
    
def validate_readonly_db_env() -> None:
    required = [
        'RO_DB_USER',
        'RO_DB_PASSWORD',
        'DB_HOST',
        'DB_PORT',
        'DB_NAME'
        ]
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise EnvironmentError(f"Missing environment variables: {missing}")
    

def validate_openai_llm_env() -> None:
    required = ['OPENAI_API_KEY']
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise EnvironmentError(f"Missing environment variables: {missing}")
    

def validate_profile(profile: dict) -> None:
    if not isinstance(profile, dict):
        raise ValueError(f"profile must be a dict, got {type(profile).__name__}")
    missing = [f for f in PROFILE_FIELDS if not profile.get(f)]
    if missing:
        raise ValueError(f"profile missing required fields: {missing}")