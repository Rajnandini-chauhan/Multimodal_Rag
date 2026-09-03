import base64
import json
import logging

from app.core.config import get_settings
from app.services.nvidia_client import get_nvidia_client

settings = get_settings()
logger = logging.getLogger(__name__)


FIGURE_DESCRIPTION_PROMPT = (
    "Describe this figure from an academic/technical document in 2-4 "
    "sentences. Focus on what it depicts (a diagram, chart, screenshot, "
    "photo, etc.) and any labels, axes, or key elements visible. Be "
    "factual and specific -- this description will be used to help "
    "someone find this figure when searching the document."
)


def describe_figure(image_bytes: bytes, mime_type: str, max_retries: int = 1) -> str | None:
    """Ask NVIDIA NIM's vision model to describe a figure's visual content.

    Returns None (rather than raising) on failure, so one bad/unsupported
    image doesn't abort the whole ingestion pipeline.
    """
    b64_image = base64.b64encode(image_bytes).decode("utf-8")
    client = get_nvidia_client()

    for attempt in range(max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=settings.vision_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": FIGURE_DESCRIPTION_PROMPT},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{b64_image}"
                                },
                            },
                        ],
                    }
                ],
            )
            return response.choices[0].message.content.strip()
        except Exception as exc:
            logger.warning("describe_figure attempt %d failed: %s", attempt, exc)
            if attempt >= max_retries:
                return None


def describe_table(rows: list[list[str | None]]) -> str | None:
    """Ask NVIDIA NIM to summarize a table's structured content in prose."""
    client = get_nvidia_client()

    prompt = (
        "Summarize what this table shows in 2-3 sentences, based on its "
        "structured rows below. Mention the columns and the kind of data "
        "being compared or listed.\n\n"
        f"Table rows (JSON):\n{json.dumps(rows)[:3000]}"
    )

    try:
        response = client.chat.completions.create(
            model=settings.llm_model,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:
        logger.warning("describe_table failed: %s", exc)
        return None
