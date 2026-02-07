"""Tests for authentication endpoints: /api/auth/*"""


class TestRegister:
    """POST /api/auth/register"""

    def test_register_success(self, client):
        resp = client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "secret123",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "newuser"
        assert data["email"] == "new@example.com"
        assert "id" in data

    def test_register_duplicate_username(self, client):
        payload = {
            "username": "dupuser",
            "email": "dup1@example.com",
            "password": "secret123",
        }
        resp1 = client.post("/api/auth/register", json=payload)
        assert resp1.status_code == 200

        # Same username, different email
        payload2 = {
            "username": "dupuser",
            "email": "dup2@example.com",
            "password": "secret123",
        }
        resp2 = client.post("/api/auth/register", json=payload2)
        assert resp2.status_code == 400
        assert "already exists" in resp2.json()["detail"].lower()


class TestLogin:
    """POST /api/auth/login"""

    def test_login_success(self, client):
        # Register first
        client.post(
            "/api/auth/register",
            json={
                "username": "loginuser",
                "email": "login@example.com",
                "password": "secret123",
            },
        )
        resp = client.post(
            "/api/auth/login",
            data={"username": "loginuser", "password": "secret123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client):
        # Register first
        client.post(
            "/api/auth/register",
            json={
                "username": "wrongpw",
                "email": "wrongpw@example.com",
                "password": "secret123",
            },
        )
        resp = client.post(
            "/api/auth/login",
            data={"username": "wrongpw", "password": "badpassword"},
        )
        assert resp.status_code == 401
        assert "incorrect" in resp.json()["detail"].lower()


class TestProfile:
    """GET /api/auth/me"""

    def test_get_profile(self, client, auth_header):
        resp = client.get("/api/auth/me", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert "is_admin" in data

    def test_get_profile_unauthorized(self, client):
        resp = client.get("/api/auth/me")
        assert resp.status_code == 401
