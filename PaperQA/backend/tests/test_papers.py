import uuid
import io
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _get_auth_header(email_prefix: str = "user") -> dict:
    unique_email = f"{email_prefix}_{uuid.uuid4().hex[:8]}@example.com"
    reg_res = client.post(
        "/api/auth/register",
        json={"email": unique_email, "password": "securepassword123"},
    )
    token = reg_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_list_papers_requires_auth():
    res = client.get("/api/papers")
    assert res.status_code in (401, 403)


def test_list_papers_empty_for_new_user():
    headers = _get_auth_header()
    res = client.get("/api/papers", headers=headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_upload_invalid_file_rejected():
    headers = _get_auth_header()
    # Sending plain text file as a fake PDF
    file_content = b"This is not a real PDF document."
    res = client.post(
        "/api/papers/upload",
        headers=headers,
        files={"file": ("fake.pdf", io.BytesIO(file_content), "application/pdf")},
    )
    assert res.status_code == 400


def test_get_paper_status_not_found():
    headers = _get_auth_header()
    random_id = str(uuid.uuid4())
    res = client.get(f"/api/papers/{random_id}/status", headers=headers)
    assert res.status_code == 404
