import json
import logging

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector

from core.config import (
    HN_JOB_POSTING_TABLE_NAME,
    HN_JOBS_FILENAME,
    HN_RAW_DATA_PATH,
    OPENAI_EMBEDDING_MODEL,
)
from core.logging import setup_logging
from core.validators import validate_openai_llm_env
from ingestion.db import get_connection_string

logger = logging.getLogger(__name__)

DEFAULT_SOURCE = HN_RAW_DATA_PATH + HN_JOBS_FILENAME


def load_hn_data(source: str = DEFAULT_SOURCE) -> tuple[list, list]:
    with open(source, "r") as f:
        json_data = json.load(f)
    texts = [p["text"] for p in json_data]
    metadatas = [
        {"id": p["id"], "author": p["author"], "created_at": p["created_at"]} for p in json_data
    ]
    return texts, metadatas


def load_hn_postings(
    texts: list, metadatas: list, collection: str = HN_JOB_POSTING_TABLE_NAME
) -> None:
    PGVector.from_texts(
        texts=texts,
        metadatas=metadatas,
        embedding=OpenAIEmbeddings(model=OPENAI_EMBEDDING_MODEL),
        connection=get_connection_string(),
        collection_name=collection,
        pre_delete_collection=True,
    )


def embed_postings(
    source: str = DEFAULT_SOURCE, collection: str = HN_JOB_POSTING_TABLE_NAME
) -> None:
    setup_logging()
    try:
        load_dotenv()
        validate_openai_llm_env()
        texts, metadatas = load_hn_data(source)
        logger.info("hn_embed.loaded", extra={"posting_count": len(texts)})
        load_hn_postings(texts, metadatas, collection)
        logger.info("hn_embed.done", extra={"collection": collection})
    except EnvironmentError as e:
        raise EnvironmentError(f"Configuration error: {e}")
    except Exception as e:
        raise Exception(f"Unexpected error: {e}")
