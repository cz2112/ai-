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

    def test_admin_can_view_any_upload_detail_and_export(self, client, admin_auth_header, test_upload):
        detail_resp = client.get(f"/api/uploads/{test_upload}", headers=admin_auth_header)
        assert detail_resp.status_code == 200
        detail_data = detail_resp.json()
        assert detail_data["id"] == test_upload
        assert detail_data["filename"] == "test_notes.pdf"

        export_resp = client.get(f"/api/uploads/{test_upload}/export", headers=admin_auth_header)
        assert export_resp.status_code == 200
        assert "# test_notes.pdf" in export_resp.text
        assert "machine learning" in export_resp.text
