import uuid
from datetime import datetime, timezone
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.database.session import SessionLocal
from app.main import app
from app.models.chat_message import ChatMessage
from app.models.paper import Paper
from app.models.user import User

client = TestClient(app)


def _create_user_and_token(email_prefix: str = "chatuser") -> tuple[User, dict]:
    db = SessionLocal()
    try:
        unique_email = f"{email_prefix}_{uuid.uuid4().hex[:8]}@example.com"
        reg_res = client.post(
            "/api/auth/register",
            json={"email": unique_email, "password": "securepassword123"},
        )
        token = reg_res.json()["access_token"]
        user = db.query(User).filter(User.email == unique_email).first()
        return user, {"Authorization": f"Bearer {token}"}
    finally:
        db.close()


def _create_mock_paper(owner_id: uuid.UUID) -> Paper:
    db = SessionLocal()
    try:
        paper = Paper(
            owner_id=owner_id,
            original_filename="chat_test_paper.pdf",
            storage_path="mock/chat_test_paper.pdf",
            file_size_bytes=2048,
            page_count=5,
        )
        db.add(paper)
        db.commit()
        db.refresh(paper)
        return paper
    finally:
        db.close()


def test_create_and_list_chat_sessions():
    user, headers = _create_user_and_token("session_owner")
    paper = _create_mock_paper(user.id)

    # 1. Create a session
    create_res = client.post(
        f"/api/papers/{paper.id}/sessions",
        headers=headers,
        json={"title": "Analysis Session 1"},
    )
    assert create_res.status_code == 201, create_res.text
    session_data = create_res.json()
    assert session_data["title"] == "Analysis Session 1"
    assert session_data["paper_id"] == str(paper.id)
    session_id = session_data["id"]

    # 2. List sessions for paper
    list_res = client.get(f"/api/papers/{paper.id}/sessions", headers=headers)
    assert list_res.status_code == 200
    sessions = list_res.json()
    assert len(sessions) >= 1
    assert any(s["id"] == session_id for s in sessions)


def test_get_session_detail_and_messages():
    user, headers = _create_user_and_token("detail_owner")
    paper = _create_mock_paper(user.id)

    create_res = client.post(
        f"/api/papers/{paper.id}/sessions",
        headers=headers,
        json={"title": "Detail Session"},
    )
    session_id = create_res.json()["id"]

    # Get session details
    detail_res = client.get(f"/api/sessions/{session_id}/messages", headers=headers)
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert detail_data["id"] == session_id
    assert "messages" in detail_data
    assert isinstance(detail_data["messages"], list)


def test_send_chat_message_mocked():
    user, headers = _create_user_and_token("msg_owner")
    paper = _create_mock_paper(user.id)

    create_res = client.post(
        f"/api/papers/{paper.id}/sessions",
        headers=headers,
        json={"title": "Agent Session"},
    )
    session_id = create_res.json()["id"]

    # Mock run_paper_agent to verify router contract without external LLM calls
    mock_msg = ChatMessage(
        id=uuid.uuid4(),
        session_id=uuid.UUID(session_id),
        role="assistant",
        content="This is a synthesized test response with citations.",
        sources=[1, 2],
        figures=[1],
        tables=[],
        visualization_spec=None,
        created_at=datetime.now(timezone.utc),
    )

    with patch("app.api.routes.chat.run_paper_agent", return_value=mock_msg):
        msg_res = client.post(
            f"/api/sessions/{session_id}/messages",
            headers=headers,
            json={"content": "What is the key finding?"},
        )
        assert msg_res.status_code == 200, msg_res.text
        msg_data = msg_res.json()
        assert msg_data["role"] == "assistant"
        assert "synthesized test response" in msg_data["content"]
        assert msg_data["sources"] == [1, 2]
        assert msg_data["figures"] == [1]


def test_delete_chat_session():
    user, headers = _create_user_and_token("del_owner")
    paper = _create_mock_paper(user.id)

    create_res = client.post(
        f"/api/papers/{paper.id}/sessions",
        headers=headers,
        json={"title": "To Delete"},
    )
    session_id = create_res.json()["id"]

    # Delete session
    del_res = client.delete(f"/api/sessions/{session_id}", headers=headers)
    assert del_res.status_code == 204

    # Verify 404 after deletion
    get_res = client.get(f"/api/sessions/{session_id}/messages", headers=headers)
    assert get_res.status_code == 404


def test_chat_cross_user_isolation():
    user_a, headers_a = _create_user_and_token("user_a")
    _user_b, headers_b = _create_user_and_token("user_b")
    paper_a = _create_mock_paper(user_a.id)

    # User A creates a session
    create_res = client.post(
        f"/api/papers/{paper_a.id}/sessions",
        headers=headers_a,
        json={"title": "User A Private Chat"},
    )
    session_id = create_res.json()["id"]

    # User B cannot access User A's session
    b_res = client.get(f"/api/sessions/{session_id}/messages", headers=headers_b)
    assert b_res.status_code == 404

    # User B cannot create a session on User A's paper
    b_create_res = client.post(
        f"/api/papers/{paper_a.id}/sessions",
        headers=headers_b,
        json={"title": "Intruder Session"},
    )
    assert b_create_res.status_code == 404
