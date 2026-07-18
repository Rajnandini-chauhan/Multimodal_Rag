import chromadb
from sentence_transformers import SentenceTransformer

from app.core.config import get_settings
from app.services.chunking import Chunk

settings = get_settings()

# Loaded once per process -- loading the model is slow, embedding calls are fast.
_embedding_model: SentenceTransformer | None = None
_chroma_client: chromadb.ClientAPI | None = None






def get_embedding_model() -> SentenceTransformer:
    global _embedding_model
    if _embedding_model is None:
        model_name = settings.embedding_model.removeprefix("sentence-transformers/")
        _embedding_model = SentenceTransformer(model_name)
    return _embedding_model


def get_chroma_client() -> chromadb.ClientAPI:
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
    return _chroma_client


def get_collection_name(paper_id: str) -> str:
    """One ChromaDB collection per paper -- keeps each paper's chunks fully
    isolated, so deleting a paper later is just dropping its collection."""
    return f"paper_{paper_id}"


def index_chunks(paper_id: str, chunks: list[Chunk]) -> int:
    """Embed and store chunks for a paper in its own ChromaDB collection.

    Returns the number of chunks indexed.
    """
    if not chunks:
        return 0

    model = get_embedding_model()
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
    embeddings = model.encode(texts, show_progress_bar=False).tolist()

    ids = [f"{paper_id}_{i}" for i in range(len(chunks))]
    metadatas = [{"page_number": c.page_number} for c in chunks]

    collection.add(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)

    return len(chunks)