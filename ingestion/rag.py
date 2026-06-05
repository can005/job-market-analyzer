from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector

from core.config import HN_JOB_POSTING_TABLE_NAME, OPENAI_EMBEDDING_MODEL
from ingestion.db import get_connection_string


def get_vectorstore() -> PGVector:
    return PGVector(
        embeddings=OpenAIEmbeddings(model=OPENAI_EMBEDDING_MODEL),
        connection=get_connection_string(),
        collection_name=HN_JOB_POSTING_TABLE_NAME,
    )
