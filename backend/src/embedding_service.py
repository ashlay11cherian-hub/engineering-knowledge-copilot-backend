import os
from typing import Iterable

import numpy as np
from dotenv import load_dotenv
from google import genai

EMBEDDING_MODEL = "gemini-embedding-2"
OUTPUT_DIMENSIONALITY = 768
DEFAULT_GENERATION_MODEL = "gemini-3.6-flash"


class EmbeddingConfigurationError(RuntimeError):
    pass


def get_client() -> genai.Client:
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not api_key or api_key == "replace_with_your_key":
        raise EmbeddingConfigurationError(
            "GEMINI_API_KEY is missing. Copy .env.example to .env "
            "and add your Google AI Studio API key."
        )

    return genai.Client(api_key=api_key)


def get_generation_model() -> str:
    load_dotenv()
    return (
        os.getenv(
            "GEMINI_GENERATION_MODEL",
            DEFAULT_GENERATION_MODEL,
        ).strip()
        or DEFAULT_GENERATION_MODEL
    )


def get_minimum_semantic_score(default: float = 0.40) -> float:
    load_dotenv()
    raw_value = os.getenv(
        "SEMANTIC_MINIMUM_SCORE",
        str(default),
    ).strip()

    try:
        value = float(raw_value)
    except ValueError:
        return default

    return min(max(value, 0.0), 1.0)


def _extract_values(response) -> list[float]:
    if not getattr(response, "embeddings", None):
        raise RuntimeError(
            "The embedding API returned no embeddings."
        )

    embedding = response.embeddings[0]
    values = getattr(embedding, "values", None)

    if values is None:
        raise RuntimeError(
            "The embedding response did not contain values."
        )

    return [float(value) for value in values]


def embed_document(text: str, client: genai.Client) -> list[float]:
    instructed_text = (
        "Represent this automotive engineering document for "
        "semantic retrieval. Preserve root causes, corrective "
        "actions, approvals, program names, risks, costs, "
        "revisions, decisions, and document status.\n\n"
        f"{text}"
    )
    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=instructed_text,
        config={
            "output_dimensionality": OUTPUT_DIMENSIONALITY
        },
    )
    return _extract_values(response)


def embed_query(text: str, client: genai.Client) -> list[float]:
    instructed_text = (
        "Represent this Program Manager search question for "
        "retrieving the most relevant automotive engineering "
        "evidence.\n\n"
        f"{text}"
    )
    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=instructed_text,
        config={
            "output_dimensionality": OUTPUT_DIMENSIONALITY
        },
    )
    return _extract_values(response)


def cosine_similarity(
    vector_a: Iterable[float],
    vector_b: Iterable[float],
) -> float:
    a = np.asarray(list(vector_a), dtype=float)
    b = np.asarray(list(vector_b), dtype=float)

    if a.shape != b.shape:
        raise ValueError("Vectors must have the same shape.")

    denominator = np.linalg.norm(a) * np.linalg.norm(b)
    if denominator == 0:
        return 0.0

    return float(np.dot(a, b) / denominator)
