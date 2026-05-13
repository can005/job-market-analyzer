from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_postgres import PGVector

from ingestion.config import HN_JOB_POSTING_TABLE_NAME, OPENAI_CHAT_MODEL, OPENAI_EMBEDDING_MODEL
from ingestion.db import get_connection_string
from ingestion.validators import validate_openai_llm_env


def get_vectorstore() -> PGVector:
    return PGVector(
        embeddings=OpenAIEmbeddings(model=OPENAI_EMBEDDING_MODEL),
        connection=get_connection_string(),
        collection_name= HN_JOB_POSTING_TABLE_NAME,
    )

def get_chat_llm() -> ChatOpenAI:
    return ChatOpenAI(model=OPENAI_CHAT_MODEL, temperature=0)

def query(prompt: str, k: int = 5) -> list:
    vectorstore = get_vectorstore()
    return vectorstore.similarity_search(prompt, k=k)

def answer_question(prompt: str, k = 5) -> dict :
    docs = query(prompt,k)
    context =  "\n\n".join(doc.page_content for doc in docs)

    llm = get_chat_llm()
    response = llm.invoke(
        f"Use the context below to answer the question. \n\n"
        f"Context: \n{context}\n\n"
        f"Question: {prompt}"
    )
    return {
        "question": prompt,
        "answer": response.content,
        "contexts": [doc.page_content for doc in docs]
    }




def main() -> None:
    try:
        load_dotenv()
        validate_openai_llm_env()
        results = answer_question("AI engineering roles using Python and LLMs")
        print(results)
    except EnvironmentError as e:
        raise EnvironmentError(f"Configuration error: {e}")
    except Exception as e:
        raise Exception(f"Unexpected error: {e}")


if __name__ == '__main__':
    main()