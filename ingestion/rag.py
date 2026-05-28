from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_postgres import PGVector

from core.config import HN_JOB_POSTING_TABLE_NAME, OPENAI_CHAT_MODEL, OPENAI_EMBEDDING_MODEL
from core.validators import validate_openai_llm_env
from ingestion.db import get_connection_string

system_msg = (
    "You answer questions about job postings using only the provided context. "
    "Do not use outside knowledge. "
    "If the context does not contain the answer, say so explicitly. "
    "Be concise."
)

human_msg = "Context:\n{context}\n\nQuestion: {question}"


prompt_template = ChatPromptTemplate.from_messages(
    [
        ("system", system_msg),
        ("human", human_msg),
    ]
)


def get_vectorstore() -> PGVector:
    return PGVector(
        embeddings=OpenAIEmbeddings(model=OPENAI_EMBEDDING_MODEL),
        connection=get_connection_string(),
        collection_name=HN_JOB_POSTING_TABLE_NAME,
    )


def get_chat_llm() -> ChatOpenAI:
    return ChatOpenAI(model=OPENAI_CHAT_MODEL, temperature=0)


def query(prompt: str, k: int = 5) -> list:
    vectorstore = get_vectorstore()
    return vectorstore.similarity_search(prompt, k=k)


def answer_question(prompt: str, k=5) -> dict:
    docs = query(prompt, k)
    context = "\n\n".join(doc.page_content for doc in docs)

    llm = get_chat_llm()
    messages = prompt_template.format_messages(context=context, question=prompt)
    response = llm.invoke(messages)
    return {
        "question": prompt,
        "answer": response.content,
        "contexts": [doc.page_content for doc in docs],
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


if __name__ == "__main__":
    main()
