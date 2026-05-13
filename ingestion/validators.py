import os


def validate_db_env() -> None:
    
    required = ['DB_USER', 
                'DB_PASSWORD', 
                'DB_HOST', 
                'DB_PORT', 
                'DB_NAME', 
                ]
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise EnvironmentError(f"Missing environment variables: {missing}")
    

def validate_openai_llm_env() -> None:
    required = ['OPENAI_API_KEY']
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise EnvironmentError(f"Missing environment variables: {missing}")