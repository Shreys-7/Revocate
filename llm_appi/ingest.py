
import re
from pathlib import Path

import chromadb
from pypdf import PdfReader


# Paths
BASE_DIR = Path(__file__).resolve().parent
PDF_PATH = BASE_DIR / "data" / "Constitution.pdf"
CHROMA_PATH = BASE_DIR / "chroma_db"

COLLECTION_NAME = "constitution"
CHUNK_SIZE = 1000       # Approximate characters per chunk
CHUNK_OVERLAP = 200     # Shared characters between chunks


def read_pdf(pdf_path: Path) -> str:
    """Extract selectable text from a PDF."""
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    reader = PdfReader(str(pdf_path))
    pages = []

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            pages.append(f"\n[Page {page_number}]\n{text}")

    full_text = "\n".join(pages)

    if not full_text.strip():
        raise ValueError(
            "No selectable text found. This PDF may be scanned "
            "and require OCR."
        )

    return full_text


def clean_text(text: str) -> str:
    """Normalize whitespace without removing paragraph boundaries."""
    text = text.replace("\x00", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_into_chunks(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[str]:
    """Split text into overlapping chunks, preferring paragraph boundaries."""
    if overlap >= chunk_size:
        raise ValueError("Overlap must be smaller than chunk size.")

    chunks = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))

        if end < len(text):
            # Prefer ending at a paragraph or sentence boundary.
            boundary = max(
                text.rfind("\n\n", start, end),
                text.rfind(". ", start, end),
                text.rfind("\n", start, end),
            )
            if boundary > start + chunk_size // 2:
                end = boundary + 1

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = max(end - overlap, start + 1)

    return chunks


def ingest_pdf():
    print(f"Reading PDF: {PDF_PATH}")

    text = clean_text(read_pdf(PDF_PATH))
    chunks = split_into_chunks(text)

    print(f"Extracted {len(text):,} characters")
    print(f"Created {len(chunks)} chunks")

    client = chromadb.PersistentClient(path=str(CHROMA_PATH))

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"description": "Constitution PDF knowledge base"},
    )

    # Remove old chunks from this source before re-indexing.
    collection.delete(where={"source": PDF_PATH.name})

    batch_size = 100

    for start in range(0, len(chunks), batch_size):
        batch = chunks[start:start + batch_size]
        start_index = start

        collection.upsert(
            ids=[
                f"constitution-{i}"
                for i in range(start_index, start_index + len(batch))
            ],
            documents=batch,
            metadatas=[
                {
                    "source": PDF_PATH.name,
                    "chunk_index": i,
                }
                for i in range(start_index, start_index + len(batch))
            ],
        )

    print(f"Successfully indexed {len(chunks)} chunks.")
    print(f"ChromaDB location: {CHROMA_PATH}")
    print(f"Collection: {COLLECTION_NAME}")


if __name__ == "__main__":
    ingest_pdf()
