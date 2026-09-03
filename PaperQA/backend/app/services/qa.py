from dataclasses import dataclass, field

from app.core.config import get_settings
from app.services.indexing import (
    embed_texts,
    get_chroma_client,
    get_collection_name,
    get_multimodal_collection_name,
)
from app.services.nvidia_client import get_nvidia_client

settings = get_settings()


@dataclass
class RetrievedItem:
    text: str  # chunk text, or a figure/table's generated description
    page_number: int
    content_type: str = "text"  # "text" | "figure" | "table"
    figure_number: int | None = None
    table_number: int | None = None
    distance: float = 0.0


@dataclass
class AnswerResult:
    answer: str
    sources: list[int] = field(default_factory=list)  # page numbers
    figures: list[int] = field(default_factory=list)  # figure numbers cited
    tables: list[int] = field(default_factory=list)  # table numbers cited


def retrieve_relevant_content(
    paper_id: str, question: str, top_k_text: int = 5, top_k_multimodal: int = 3
) -> list[RetrievedItem]:
    """Dense retrieval across BOTH the plain-text chunk collection and the
    figure/table description collection, then merge and rerank by distance
    (lower = more similar) so the most relevant items win regardless of
    which modality they came from.
    """
    client = get_chroma_client()
    # NIM's asymmetric embeddings: "query" at retrieval, "passage" at index.
    query_embedding = embed_texts([question], input_type="query")

    items: list[RetrievedItem] = []

    text_collection = client.get_or_create_collection(name=get_collection_name(paper_id))
    text_results = text_collection.query(
        query_embeddings=query_embedding, n_results=top_k_text
    )
    for doc, meta, dist in zip(
        text_results["documents"][0] if text_results["documents"] else [],
        text_results["metadatas"][0] if text_results["metadatas"] else [],
        text_results["distances"][0] if text_results["distances"] else [],
    ):
        items.append(
            RetrievedItem(
                text=doc, page_number=meta["page_number"], content_type="text", distance=dist
            )
        )

    mm_collection = client.get_or_create_collection(
        name=get_multimodal_collection_name(paper_id)
    )
    if mm_collection.count() > 0:
        mm_results = mm_collection.query(
            query_embeddings=query_embedding,
            n_results=min(top_k_multimodal, mm_collection.count()),
        )
        for doc, meta, dist in zip(
            mm_results["documents"][0] if mm_results["documents"] else [],
            mm_results["metadatas"][0] if mm_results["metadatas"] else [],
            mm_results["distances"][0] if mm_results["distances"] else [],
        ):
            items.append(
                RetrievedItem(
                    text=doc,
                    page_number=meta["page_number"],
                    content_type=meta.get("content_type", "figure"),
                    figure_number=meta.get("figure_number"),
                    table_number=meta.get("table_number"),
                    distance=dist,
                )
            )

    items.sort(key=lambda i: i.distance)
    return items


def _format_context_block(item: RetrievedItem) -> str:
    if item.content_type == "figure":
        label = f"Figure {item.figure_number}" if item.figure_number else "Figure"
        return f"[Page {item.page_number}, {label} -- visual description]\n{item.text}"
    if item.content_type == "table":
        label = f"Table {item.table_number}" if item.table_number else "Table"
        return f"[Page {item.page_number}, {label} -- content summary]\n{item.text}"
    return f"[Page {item.page_number}, Text]\n{item.text}"


def generate_answer(question: str, items: list[RetrievedItem]) -> AnswerResult:
    """Generate a grounded answer from retrieved text/figure/table content,
    instructed to cite pages AND figure/table numbers when relevant.
    """
    if not items:
        return AnswerResult(
            answer="I couldn't find relevant content in this paper to answer that question."
        )

    context_blocks = "\n\n".join(_format_context_block(i) for i in items)

    prompt = (
        "You are answering a question using only the excerpts below from a "
        "document. Excerpts may be plain text, or descriptions of figures "
        "and tables (since the original images/tables have already been "
        "interpreted for you). Each excerpt is labeled with its page number "
        "and, if applicable, its figure or table number.\n\n"
        "Rules:\n"
        "- Only use information from the excerpts. Do not use outside knowledge.\n"
        "- If the excerpts don't contain the answer, say so clearly.\n"
        "- If your answer relies on a figure or table, explicitly say so "
        "(e.g. 'as shown in Figure 3...') in addition to citing the page.\n"
        "- Cite page numbers like (page 3).\n\n"
        f"Excerpts:\n{context_blocks}\n\n"
        f"Question: {question}\n\n"
        "Answer:"
    )

    client = get_nvidia_client()
    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[{"role": "user", "content": prompt}],
    )
    answer_text = response.choices[0].message.content.strip()

    sources = sorted({i.page_number for i in items})
    figures = sorted({i.figure_number for i in items if i.figure_number is not None})
    tables = sorted({i.table_number for i in items if i.table_number is not None})

    return AnswerResult(answer=answer_text, sources=sources, figures=figures, tables=tables)
