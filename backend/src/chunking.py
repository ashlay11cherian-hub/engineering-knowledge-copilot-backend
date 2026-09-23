from typing import Any


def chunk_text(
    text: str,
    chunk_size_words: int = 120,
    overlap_words: int = 25,
) -> list[str]:
    """Split text into overlapping word-based chunks."""
    if chunk_size_words <= 0:
        raise ValueError("chunk_size_words must be positive")
    if overlap_words < 0:
        raise ValueError("overlap_words cannot be negative")
    if overlap_words >= chunk_size_words:
        raise ValueError(
            "overlap_words must be smaller than chunk_size_words"
        )

    words = text.split()
    if not words:
        return []

    chunks: list[str] = []
    step = chunk_size_words - overlap_words

    for start in range(0, len(words), step):
        end = min(start + chunk_size_words, len(words))
        chunk = " ".join(words[start:end]).strip()
        if chunk:
            chunks.append(chunk)
        if end == len(words):
            break

    return chunks


def create_document_chunks(
    documents: list[dict[str, Any]],
    chunk_size_words: int = 120,
    overlap_words: int = 25,
) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []

    for document in documents:
        text_chunks = chunk_text(
            document.get("content", ""),
            chunk_size_words=chunk_size_words,
            overlap_words=overlap_words,
        )

        for index, chunk in enumerate(text_chunks):
            chunks.append(
                {
                    "chunk_id": (
                        f"{document['document_id']}-CHUNK-{index + 1}"
                    ),
                    "document_id": document["document_id"],
                    "title": document["title"],
                    "source_type": document["source_type"],
                    "program_id": document.get("program_id"),
                    "classification": document.get("classification"),
                    "allowed_roles": document.get("allowed_roles", []),
                    "revision": document.get("revision"),
                    "authority_rank": document.get(
                        "authority_rank", 0
                    ),
                    "document_status": document.get(
                        "document_status", "current"
                    ),
                    "text": chunk,
                }
            )

    return chunks
