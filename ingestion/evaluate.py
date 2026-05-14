


from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from ragas import EvaluationDataset, evaluate
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import (
    Faithfulness,
    LLMContextPrecisionWithReference,
    ResponseRelevancy,
)

from ingestion.config import OPENAI_CHAT_MODEL, OPENAI_EMBEDDING_MODEL
from ingestion.evaluation_questions import EVAL_QUESTIONS
from ingestion.rag import answer_question
from ingestion.validators import validate_openai_llm_env


def build_eval_dataset(eval_questions: list[dict]) -> EvaluationDataset:
    rows = []
    for item in eval_questions:
        result = answer_question(item["question"])

        contexts = result["contexts"]
        if isinstance(contexts, str):
            contexts = [contexts]
        else:
            contexts = [str(c) for c in contexts]

        rows.append({
            "user_input": result["question"],
            "response": result["answer"],
            "retrieved_contexts": contexts,
            "reference": item["ground_truth"],
        })
    return EvaluationDataset.from_list(rows)


def run_evaluation():
    llm = LangchainLLMWrapper(ChatOpenAI(model=OPENAI_CHAT_MODEL))
    embeddings = LangchainEmbeddingsWrapper(
        OpenAIEmbeddings(model=OPENAI_EMBEDDING_MODEL)
    )

    dataset = build_eval_dataset(EVAL_QUESTIONS)
    # TODO: Migrate to `experiment()` + `ragas.metrics.collections`
    return evaluate(
        dataset=dataset,
        metrics=[
            Faithfulness(),
            ResponseRelevancy(),
            LLMContextPrecisionWithReference(),
        ],
        llm=llm,
        embeddings=embeddings,
    )


def main() -> None:
    load_dotenv()
    validate_openai_llm_env()
    results = run_evaluation()
    print(results)


if __name__ == "__main__":
    main()