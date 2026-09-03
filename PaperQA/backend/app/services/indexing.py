"""Embedding + ChromaDB indexing.

Embeddings now come from NVIDIA NIM (`meta/muse-glimmer-30b`) via the
OpenAI-compatible `/v1/embeddings` endpoint, replacing the local
sentence-transformers model. The model exposes two input types --
"passage" for documents being indexed and "query" for retrieval-time
embeddings -- so we route them through the same client.
"""

import chromadb

from app.core.config import get_settings
from app.services.chunking import Chunk
from app.services.nvidia_client import get_nvidia_client

settings = get_settings()

# ChromaDB client is cached per process; opening a persistent client is
# moderately expensive so we reuse the handle across ingest + query calls.
_chroma_client: chromadb.ClientAPI | None = None


def get_chroma_client() -> chromadb.ClientAPI:
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
    return _chroma_client


def get_collection_name(paper_id: str) -> str:
    """One ChromaDB collection per paper -- keeps each paper's chunks fully
    isolated, so deleting a paper later is just dropping its collection."""
    return f"paper_{paper_id}"


def get_multimodal_collection_name(paper_id: str) -> str:
    """Separate collection for figure/table description embeddings, kept
    apart from plain text chunks so retrieval can query each independently
    before merging results (Milestone 8's multimodal reranking)."""
    return f"paper_{paper_id}_multimodal"


def embed_texts(texts: list[str], input_type: str | None = None) -> list[list[float]]:
    """Embed a batch of texts via NVIDIA NIM's /v1/embeddings.

    input_type must be "passage" when indexing documents and "query" at
    retrieval time -- the model uses asymmetric embeddings and the two
    types land in different regions of the vector space.
    """
    if not texts:
        return []

    client = get_nvidia_client()
    type_arg = input_type or settings.embedding_input

    # NIM returns embeddings as float lists; the openai SDK exposes them
    # under .data[i].embedding. Batching is handled client-side; NIM's
    # embedding endpoint accepts reasonably large batches in one call.
    response = client.embeddings.create(
        model=settings.embedding_model,
        input=texts,
        extra_body={"input_type": type_arg},
    )
    return [item.embedding for item in response.data]


def index_chunks(paper_id: str, chunks: list[Chunk]) -> int:
    """Embed and store chunks for a paper in its own ChromaDB collection.

    Returns the number of chunks indexed.
    """
    if not chunks:
        return 0

    client = get_chroma_client()

    # Drop any existing collection first -- re-indexing should fully replace
    # the paper's chunks, not accumulate duplicates or leave stale chunks
    # behind if the chunking logic changed since the last index.
    try:
        client.delete_collection(name=get_collection_name(paper_id))
    except Exception:
        pass  # collection may not exist yet on first index -- fine

    collection = client.get_or_create_collection(name=get_collection_name(paper_id))

    texts = [c.text for c in chunks]
    embeddings = embed_texts(texts, input_type="passage")

    ids = [f"{paper_id}_{i}" for i in range(len(chunks))]
    metadatas = [{"page_number": c.page_number} for c in chunks]

    collection.add(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)

    return len(chunks)
