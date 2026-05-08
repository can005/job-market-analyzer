import json
import os
from datetime import datetime

from dotenv import load_dotenv
from openai import OpenAI
from sqlalchemy.orm import Session

from ingestion.config import HN_JOBS_FILENAME, HN_RAW_DATA_PATH
from ingestion.db import bulk_upsert, get_engine
from ingestion.models import Base, HNJobPosting

load_dotenv()

def validate_llm_env() -> None:
    required = ['OPENAI_API_KEY' ]
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise EnvironmentError(f"Missing environment variables: {missing}")
    

def load_and_batch_data() -> list:
    json_data = {}
    with open (HN_RAW_DATA_PATH +HN_JOBS_FILENAME, 'r') as f: 
        json_data = json.load(f)

    batches = []
    if json_data:
        for i in range(0, len(json_data), 500):
            batch = json_data[i:i+500]
            batches.append(batch)
    
    return batches

def embed_batches(client: OpenAI, batches: list) -> list:
    results = []
    for batch in batches:
        texts = [posting["text"] for posting in batch]
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=texts
        )
        for posting, embedding_obj in zip(batch, response.data):
            results.append({
                **posting,
                "embedding": embedding_obj.embedding
            })
    return results

def load_hn_postings(session: Session, postings: list) -> None:
    records = [
        {
            "id": p["id"],
            "author": p["author"],
            "text": p["text"],
            "created_at": datetime.fromisoformat(p["created_at"].replace("Z", "+00:00")),
            "embedding": p["embedding"]
        }
        for p in postings
    ]
    bulk_upsert(session, HNJobPosting, records, ["id"])

def main() -> None:

    try:
        validate_llm_env()
        batched_data = load_and_batch_data()
        client = OpenAI()
        embeddings = embed_batches(client, batches=batched_data) 
        engine = get_engine()
        Base.metadata.create_all(engine)
        print("Database tables verified")
        with Session(engine) as session:
            load_hn_postings(session, embeddings)

        print("Done embedding")
    except EnvironmentError as e:
        raise EnvironmentError(f"Configuration error: {e}")
    except Exception as e:
        raise Exception(f"Unexpected error: {e}")

if __name__ == '__main__':
    main()