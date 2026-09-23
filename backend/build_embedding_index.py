from pathlib import Path

from backend.src.chunking import create_document_chunks
from backend.src.document_loader import load_documents
from backend.src.embedding_service import embed_document, get_client
from backend.src.vector_index import save_index


BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
INDEX_FILE = BASE_DIR / "embedding_index.json"


def main() -> None:
    documents = load_documents(DATA_DIR)

    chunks = create_document_chunks(
        documents,
        chunk_size_words=120,
        overlap_words=25,
    )

    client = get_client()

    index_entries = []

    print(f"Documents loaded: {len(documents)}")
    print(f"Creating embeddings for {len(chunks)} chunks...")

    for position, chunk in enumerate(chunks, start=1):
        print(
            f"[{position}/{len(chunks)}] "
            f"{chunk['chunk_id']} — {chunk['title']}"
        )

        embedding_text = (
            f"Title: {chunk['title']}\n"
            f"Source type: {chunk['source_type']}\n"
            f"Program: {chunk['program_id']}\n"
            f"Revision: {chunk['revision']}\n"
            f"Status: {chunk.get('document_status', 'current')}\n"
            f"Content: {chunk['text']}"
        )

        entry = chunk.copy()

        entry["embedding"] = embed_document(
            embedding_text,
            client,
        )

        index_entries.append(entry)

    save_index(
        index_entries,
        INDEX_FILE,
    )

    print()
    print(f"Saved semantic index to: {INDEX_FILE}")
    print(f"Indexed chunks: {len(index_entries)}")


if __name__ == "__main__":
    main()
