import uuid
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_register_and_login_flow():
    unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    password = "securepassword123"

    # 1. Register new user
    reg_res = client.post(
        "/api/auth/register",
        json={"email": unique_email, "password": password},
    )
    assert reg_res.status_code == 201, reg_res.text
    reg_data = reg_res.json()
    assert "access_token" in reg_data
    assert reg_data["token_type"] == "bearer"
    token = reg_data["access_token"]

    # 2. Reject duplicate email
    dup_res = client.post(
        "/api/auth/register",
        json={"email": unique_email, "password": password},
    )
    assert dup_res.status_code == 400

    # 3. Login with correct credentials
    login_res = client.post(
        "/api/auth/login",
        json={"email": unique_email, "password": password},
    )
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert "access_token" in login_data

    # 4. Login with invalid password
    bad_login_res = client.post(
        "/api/auth/login",
        json={"email": unique_email, "password": "wrongpassword"},
    )
    assert bad_login_res.status_code == 401

    # 5. Access /api/auth/me with bearer token
    me_res = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["email"] == unique_email
    assert "id" in me_data


def test_auth_me_unauthorized():
    res = client.get("/api/auth/me")
    assert res.status_code in (401, 403)
