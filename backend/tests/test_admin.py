"""Tests for admin endpoints: /api/admin/*"""


class TestAdminUsers:
    """GET /api/admin/users"""

    def test_admin_list_users(self, client, admin_auth_header):
        resp = client.get("/api/admin/users", headers=admin_auth_header)
        assert resp.status_code == 200
        data = resp.json()
        # At least the admin user should be present
        assert isinstance(data, list)
        assert len(data) >= 1
        usernames = [u["username"] for u in data]
        assert "adminuser" in usernames

    def test_non_admin_cannot_access(self, client, auth_header):
        resp = client.get("/api/admin/users", headers=auth_header)
        assert resp.status_code == 403
        assert "admin" in resp.json()["detail"].lower()
