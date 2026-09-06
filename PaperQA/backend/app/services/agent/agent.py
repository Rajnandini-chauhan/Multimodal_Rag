import json
import logging
import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.chat_message import ChatMessage
from app.models.chat_session import ChatSession
from app.services.agent.tool_registry import TOOL_DEFINITIONS, execute_tool_call
from app.services.nvidia_client import get_nvidia_client

settings = get_settings()
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are an expert AI research assistant analyzing academic and technical documents. "
    "You have access to specialized tools to inspect the document:\n"
    "- search_paper: Vector search for text, figure descriptions, or table summaries.\n"
    "- get_page: View extracted content on a specific page.\n"
    "- get_figure: View visual descriptions and captions of a figure.\n"
    "- get_table: View structured rows and summaries of a table.\n"
    "- explain_equation: Inspect an equation and its contextual explanation.\n"
    "- create_chart: Generate an interactive Plotly chart from a table.\n\n"
    "Rules:\n"
    "1. Always use tools to ground your answers in the paper's actual content.\n"
    "2. If asked about figures or tables, use get_figure or get_table to verify details.\n"
    "3. If asked to plot, visualize, or compare data from a table, use create_chart.\n"
    "4. Be objective, precise, and clear."
)


def run_paper_agent(
    session_id: uuid.UUID,
    user_message_text: str,
    db: Session,
    max_tool_loops: int = 3,
) -> ChatMessage:
    """Run multi-turn paper agent with tool execution loop."""
    session = db.get(ChatSession, session_id)
    if session is None:
        raise ValueError(f"ChatSession {session_id} not found.")

    paper_id_str = str(session.paper_id)

    # 1. Save user message to database
    user_msg = ChatMessage(
        session_id=session.id,
        role="user",
        content=user_message_text,
    )
    db.add(user_msg)
    db.commit()

    # 2. Build message chain from session history
    past_messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )

    api_messages: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]
    for m in past_messages[-10:]:  # Keep last 10 messages context window
        api_messages.append({"role": m.role, "content": m.content})

    client = get_nvidia_client()

    context_acc: dict[str, Any] = {
        "sources": set(),
        "figures": set(),
        "tables": set(),
        "visualization_spec": None,
    }

    # 3. Tool execution loop
    for loop in range(max_tool_loops):
        try:
            response = client.chat.completions.create(
                model=settings.llm_model,
                messages=api_messages,
                tools=TOOL_DEFINITIONS,
                tool_choice="auto",
            )
        except Exception as exc:
            logger.error("LLM call failed in agent loop: %s", exc)
            # Fallback to direct prompt if tools API isn't supported or errors out
            response = client.chat.completions.create(
                model=settings.llm_model,
                messages=api_messages,
            )
            final_text = response.choices[0].message.content or ""
            break

        msg = response.choices[0].message

        # If LLM returned tool calls
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            # Append assistant message with tool calls to history
            api_messages.append(
                {
                    "role": "assistant",
                    "content": msg.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in msg.tool_calls
                    ],
                }
            )

            # Execute tool calls
            for tc in msg.tool_calls:
                fn_name = tc.function.name
                try:
                    fn_args = json.loads(tc.function.arguments)
                except Exception:
                    fn_args = {}

                tool_output = execute_tool_call(
                    fn_name, fn_args, paper_id_str, db, context_acc
                )

                api_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": tool_output,
                    }
                )
        else:
            final_text = msg.content or ""
            break
    else:
        # Reached max loop iterations
        final_text = "I completed my analysis of the document."

    # 4. Save assistant response to DB
    sources_list = sorted(list(context_acc["sources"])) if context_acc["sources"] else None
    figures_list = sorted(list(context_acc["figures"])) if context_acc["figures"] else None
    tables_list = sorted(list(context_acc["tables"])) if context_acc["tables"] else None

    assistant_msg = ChatMessage(
        session_id=session.id,
        role="assistant",
        content=final_text,
        sources=sources_list,
        figures=figures_list,
        tables=tables_list,
        visualization_spec=context_acc["visualization_spec"],
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    return assistant_msg
