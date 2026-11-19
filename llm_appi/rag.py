
from pathlib import Path

import chromadb

# Keep this path consistent with ingest.py
BASE_DIR = Path(__file__).resolve().parent
CHROMA_PATH = BASE_DIR / "chroma_db"
COLLECTION_NAME = "constitution"


def retrieve_context(question: str, top_k: int = 4) -> str:
    """Retrieve relevant chunks from the indexed Constitution PDF."""
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))

    collection = client.get_collection(name=COLLECTION_NAME)

    results = collection.query(
        query_texts=[question],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    if not documents:
        return "No relevant passages were found in the document."

    passages = []

    for index, document in enumerate(documents):
        metadata = metadatas[index] if index < len(metadatas) else {}
        source = metadata.get("source", "Unknown source")
        chunk_index = metadata.get("chunk_index", index)

        passages.append(
            f"[Source: {source}, chunk: {chunk_index}]\n{document}"
        )

    return "\n\n---\n\n".join(passages)
