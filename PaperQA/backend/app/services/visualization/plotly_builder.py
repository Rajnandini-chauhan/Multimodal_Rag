import json
import logging
import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.content_block import ContentBlock, ContentType

logger = logging.getLogger(__name__)


def build_plotly_spec_from_table(
    db: Session,
    paper_id: str,
    table_number: int,
    chart_type: str = "bar",
) -> dict[str, Any] | None:
    """Extract table content block from DB for given paper and table_number,
    parse structured rows/cells, and build a Plotly JSON specification.
    """
    block = (
        db.query(ContentBlock)
        .filter(
            ContentBlock.paper_id == uuid.UUID(paper_id),
            ContentBlock.content_type == ContentType.TABLE,
        )
        .all()
    )

    target_block = None
    for b in block:
        if b.extra_data and b.extra_data.get("table_number") == table_number:
            target_block = b
            break

    if target_block is None and block:
        target_block = block[0]

    if target_block is None:
        return None

    # Parse rows from content (JSON array of arrays) or extra_data
    rows: list[list[Any]] = []
    if target_block.extra_data and "rows" in target_block.extra_data:
        rows = target_block.extra_data["rows"]
    else:
        try:
            rows = json.loads(target_block.content)
        except Exception:
            logger.warning("Could not parse table content JSON for block %s", target_block.id)
            return None

    if not rows or len(rows) < 2:
        return None

    headers = [str(cell) if cell is not None else f"Col {i+1}" for i, cell in enumerate(rows[0])]
    data_rows = rows[1:]

    # x-axis is usually column 0
    x_vals = [str(r[0]) if r and len(r) > 0 and r[0] is not None else f"Row {i+1}" for i, r in enumerate(data_rows)]

    traces = []
    plot_kind = chart_type.lower()
    plotly_type = "bar" if plot_kind == "bar" else "scatter"
    mode = "lines+markers" if plot_kind == "line" else None

    # Each numeric column gets a trace
    for col_idx in range(1, len(headers)):
        col_name = headers[col_idx]
        y_vals = []
        for r in data_rows:
            val = None
            if len(r) > col_idx:
                raw_val = str(r[col_idx]).replace("%", "").strip()
                try:
                    val = float(raw_val)
                except ValueError:
                    val = None
            y_vals.append(val)

        # Check if column has any numeric data
        if any(v is not None for v in y_vals):
            trace: dict[str, Any] = {
                "type": plotly_type,
                "name": col_name,
                "x": x_vals,
                "y": y_vals,
            }
            if mode:
                trace["mode"] = mode
            traces.append(trace)

    if not traces:
        return None

    title = f"Table {table_number} Visualization"
    if target_block.extra_data and target_block.extra_data.get("caption"):
        title = target_block.extra_data["caption"]

    spec = {
        "data": traces,
        "layout": {
            "title": title,
            "xaxis": {"title": headers[0]},
            "yaxis": {"title": "Value"},
            "margin": {"t": 40, "b": 40, "l": 50, "r": 20},
            "autosize": True,
        },
    }

    return spec
