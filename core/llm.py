from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from core.config import OPENAI_CHAT_MODEL, OPENAI_EMBEDDING_MODEL


def get_chat_llm() -> ChatOpenAI:
    return ChatOpenAI(model=OPENAI_CHAT_MODEL, temperature=0)


def get_embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(model=OPENAI_EMBEDDING_MODEL)


def get_structured_llm(schema, temperature: float = 0) -> ChatOpenAI:
    return ChatOpenAI(
        model=OPENAI_CHAT_MODEL,
        temperature=temperature,
    ).with_structured_output(schema)