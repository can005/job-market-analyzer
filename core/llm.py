from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from core.config import OPENAI_CHAT_MODEL, OPENAI_EMBEDDING_MODEL

DEFAULT_TIMEOUT = 30
DEFAULT_MAX_RETRIES = 2

AGENT_LOOP_TIMEOUT = 90
AGENT_LOOP_MAX_RETRIES = 3


def get_chat_llm(
    *,
    timeout: float = DEFAULT_TIMEOUT,
    max_retries: int = DEFAULT_MAX_RETRIES,
) -> ChatOpenAI:
    return ChatOpenAI(
        model=OPENAI_CHAT_MODEL,
        temperature=0,
        timeout=timeout,
        max_retries=max_retries,
    )


def get_agent_chat_llm() -> ChatOpenAI:
    return get_chat_llm(timeout=AGENT_LOOP_TIMEOUT, max_retries=AGENT_LOOP_MAX_RETRIES)


def get_embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(model=OPENAI_EMBEDDING_MODEL)


def get_structured_llm(
    schema,
    *,
    temperature: float = 0,
    timeout: float = DEFAULT_TIMEOUT,
    max_retries: int = DEFAULT_MAX_RETRIES,
) -> ChatOpenAI:
    return ChatOpenAI(
        model=OPENAI_CHAT_MODEL,
        temperature=temperature,
        timeout=timeout,
        max_retries=max_retries,
    ).with_structured_output(schema)
