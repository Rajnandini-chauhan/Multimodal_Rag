from dataclasses import dataclass

import google.generativeai as genai

from app.core.config import get_settings
from app.services.indexing import get_chroma_client, get_collection_name, get_embedding_model

settings = get_settings()

_gemini_configured = False


@dataclass
class RetrievedChunk:
    text: str
    page_number: int


@dataclass
class AnswerResult:
    answer: str
    sources: list[int]  # unique page numbers cited


def _ensure_gemini_configured() -> None:
    global _gemini_configured
    if not _gemini_configured:
        genai.configure(api_key=settings.gemini_api_key)
        _gemini_configured = True


def retrieve_relevant_chunks(
    paper_id: str, question: str, top_k: int = 5
) -> list[RetrievedChunk]:
    """Dense retrieval: embed the question, find the most similar chunks
    from this paper's ChromaDB collection."""
    model = get_embedding_model()
    client = get_chroma_client()

    collection = client.get_or_create_collection(name=get_collection_name(paper_id))

    query_embedding = model.encode([question]).tolist()
    results = collection.query(query_embeddings=query_embedding, n_results=top_k)

    documents = results["documents"][0] if results["documents"] else []
    metadatas = results["metadatas"][0] if results["metadatas"] else []

    return [
        RetrievedChunk(text=doc, page_number=meta["page_number"])
        for doc, meta in zip(documents, metadatas)
    ]


def generate_answer(question: str, chunks: list[RetrievedChunk]) -> AnswerResult:
    """Generate a grounded answer from retrieved chunks using Gemini,
    instructed to only use the provided context and cite page numbers."""
    if not chunks:
        return AnswerResult(
            answer="I couldn't find relevant content in this paper to answer that question.",
            sources=[],
        )

    _ensure_gemini_configured()

    context_blocks = "\n\n".join(
        f"[Page {c.page_number}]\n{c.text}" for c in chunks
    )

    prompt = (
        "You are answering a question using only the excerpts below from a "
        "research paper. Each excerpt is labeled with its page number.\n\n"
        "Rules:\n"
        "- Only use information from the excerpts. Do not use outside knowledge.\n"
        "- If the excerpts don't contain the answer, say so clearly.\n"
        "- Cite the page number(s) your answer comes from, like (page 3).\n\n"
        f"Excerpts:\n{context_blocks}\n\n"
        f"Question: {question}\n\n"
        "Answer:"
    )

    model = genai.GenerativeModel(settings.llm_model)
    response = model.generate_content(prompt)

    sources = sorted({c.page_number for c in chunks})

    return AnswerResult(answer=response.text.strip(), sources=sources)