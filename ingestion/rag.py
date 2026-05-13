from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector

from ingestion.config import HN_JOB_POSTING_TABLE_NAME, OPENAI_EMBEDDING_MODEL
from ingestion.db import get_connection_string
from ingestion.validators import validate_openai_llm_env


def get_vectorstore() -> PGVector:
    return PGVector(
        embeddings=OpenAIEmbeddings(model=OPENAI_EMBEDDING_MODEL),
        connection=get_connection_string(),
        collection_name= HN_JOB_POSTING_TABLE_NAME,
    )

def query(prompt: str, k: int = 5) -> list:
    vectorstore = get_vectorstore()
    return vectorstore.similarity_search(prompt, k=k)


def main() -> None:
    try:
        load_dotenv()
        validate_openai_llm_env()
        results = query("AI engineering roles using Python and LLMs")
        for i, doc in enumerate(results):
            print(f"\n--- Result {i+1} ---")
            print(doc.page_content[:300])
    except EnvironmentError as e:
        raise EnvironmentError(f"Configuration error: {e}")
    except Exception as e:
        raise Exception(f"Unexpected error: {e}")


if __name__ == '__main__':
    main()