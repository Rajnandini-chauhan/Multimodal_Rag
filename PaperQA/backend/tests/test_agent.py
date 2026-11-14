import json
import uuid
from app.database.session import SessionLocal
from app.models.content_block import ContentBlock, ContentType
from app.models.paper import Paper
from app.models.user import User
from app.services.agent.tool_registry import TOOL_DEFINITIONS, execute_tool_call
from app.services.visualization.plotly_builder import build_plotly_spec_from_table


def test_tool_definitions_structure():
    assert len(TOOL_DEFINITIONS) >= 6
    names = [t["function"]["name"] for t in TOOL_DEFINITIONS]
    assert "search_paper" in names
    assert "get_page" in names
    assert "get_figure" in names
    assert "get_table" in names
    assert "explain_equation" in names
    assert "create_chart" in names


def test_plotly_builder_numeric_table():
    db = SessionLocal()
    try:
        # Create a mock paper and content block
        user = db.query(User).first()
        if not user:
            user = User(email=f"test_{uuid.uuid4().hex[:6]}@example.com", hashed_password="pwd")
            db.add(user)
            db.commit()

        paper = Paper(
            owner_id=user.id,
            original_filename="test_mock.pdf",
            storage_path="mock/path.pdf",
            file_size_bytes=1000,
        )
        db.add(paper)
        db.commit()

        table_data = [
            ["Model", "Accuracy", "F1 Score"],
            ["BERT", 85.5, 84.2],
            ["RoBERTa", 88.0, 87.5],
        ]
        block = ContentBlock(
            paper_id=paper.id,
            content_type=ContentType.TABLE,
            page_number=2,
            content=json.dumps(table_data),
            extra_data={"table_number": 88, "rows": table_data, "caption": "Test Table"},
        )
        db.add(block)
        db.commit()

        # Test plotly chart builder
        spec = build_plotly_spec_from_table(db, str(paper.id), 88, "bar")
        assert spec is not None
        assert "data" in spec
        assert "layout" in spec
        assert len(spec["data"]) == 2  # Accuracy and F1 Score traces
        assert spec["data"][0]["type"] == "bar"

        # Cleanup
        db.delete(block)
        db.delete(paper)
        db.commit()
    finally:
        db.close()


def test_execute_tool_call_unknown():
    db = SessionLocal()
    try:
        context_acc = {"sources": set(), "figures": set(), "tables": set(), "visualization_spec": None}
        out = execute_tool_call("unknown_tool", {}, str(uuid.uuid4()), db, context_acc)
        assert "Unknown tool" in out
    finally:
        db.close()
