from pathlib import Path

from backend.services.demo_service import get_demo_users
from backend.src.auth import filter_authorized_documents
from backend.src.document_loader import load_documents
from backend.src.embedding_service import get_client
from backend.src.vector_index import load_index, semantic_search


BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
INDEX_FILE = BASE_DIR / "embedding_index.json"


TEST_CASES = [
    (
        "sarah",
        "What caused the Gen-3 wireless charger thermal failure, "
        "and what corrective action was approved?",
    ),
    (
        "alex",
        "What is the manufacturing cost per unit?",
    ),
    (
        "chris",
        "What are the product's unit economics?",
    ),
    (
        "sarah",
        "Which supplier will manufacture the redesigned coil in 2027?",
    ),
]


def main():
    documents = load_documents(DATA_DIR)
    index_entries = load_index(INDEX_FILE)
    client = get_client()

    users = {
        user.user_id: user
        for user in get_demo_users()
    }

    for user_id, query in TEST_CASES:
        user = users[user_id]

        authorized_documents = filter_authorized_documents(
            documents,
            user.model_dump(),
        )

        authorized_ids = {
            document["document_id"]
            for document in authorized_documents
        }

        # Intentionally use a low diagnostic threshold so we can see
        # the score distribution instead of hiding candidates.
        results = semantic_search(
            query=query,
            index_entries=index_entries,
            authorized_document_ids=authorized_ids,
            client=client,
            top_k=10,
            minimum_score=0.0,
        )

        print()
        print("=" * 80)
        print(f"USER: {user_id}")
        print(f"QUERY: {query}")
        print(f"AUTHORIZED DOCUMENTS: {len(authorized_ids)}")
        print("-" * 80)

        if not results:
            print("No candidates returned.")
            continue

        for position, result in enumerate(results, start=1):
            score = result.get("semantic_score")

            if score is None:
                print("Available result keys:", list(result.keys()))
                score_text = "UNKNOWN"
            else:
                score_text = f"{float(score):.4f}"

            print(
                f"{position}. "
                f"{result['document_id']} | "
                f"{result['title']} | "
                f"SCORE={score_text}"
            )


if __name__ == "__main__":
    main()
