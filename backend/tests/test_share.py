"""Tests for share endpoints: /api/share/*"""


class TestShareUpload:
    """POST /api/share/  &  GET /api/share/shared-with-me"""

    def test_share_upload(self, client, auth_header, second_auth_header, test_upload):
        # Get the second user's id
        resp = client.get("/api/auth/me", headers=second_auth_header)
        user2_id = resp.json()["id"]

        resp = client.post(
            "/api/share/",
            headers=auth_header,
            json={
                "upload_id": test_upload,
                "shared_with": user2_id,
                "message": "Check out my notes!",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["upload_id"] == test_upload
        assert data["shared_with"] == user2_id
        assert data["message"] == "Check out my notes!"

    def test_list_shared(self, client, auth_header, second_auth_header, test_upload):
        # Share publicly (shared_with=None)
        client.post(
            "/api/share/",
            headers=auth_header,
            json={"upload_id": test_upload},
        )

        # Second user should see it in shared-with-me
        resp = client.get("/api/share/shared-with-me", headers=second_auth_header)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_toggle_upload_visibility(self, client, auth_header, second_auth_header, test_upload):
        resp = client.patch(
            f"/api/share/uploads/{test_upload}/visibility",
            headers=auth_header,
            json={"is_shared": True},
        )
        assert resp.status_code == 200
        assert resp.json()["is_shared"] is True

        resp = client.get("/api/share/shared-with-me", headers=second_auth_header)
        assert resp.status_code == 200
        assert any(item["upload_id"] == test_upload for item in resp.json())


class TestStudyGroups:
    """POST /api/share/groups  &  POST /api/share/groups/{id}/join"""

    def test_create_study_group(self, client, auth_header):
        resp = client.post(
            "/api/share/groups",
            headers=auth_header,
            json={"name": "Physics 101", "description": "Study group for physics"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Physics 101"
        assert data["description"] == "Study group for physics"
        assert data["member_count"] == 1
        assert "id" in data

    def test_join_study_group(self, client, auth_header, second_auth_header):
        # First user creates a group
        resp = client.post(
            "/api/share/groups",
            headers=auth_header,
            json={"name": "Math Group", "description": "Algebra study"},
        )
        group_id = resp.json()["id"]

        # Second user joins the group
        resp = client.post(
            f"/api/share/groups/{group_id}/join",
            headers=second_auth_header,
        )
        assert resp.status_code == 200
        assert "joined" in resp.json()["detail"].lower()

    def test_group_share_visible_only_to_members(self, client, auth_header, second_auth_header, test_upload):
        resp = client.post(
            "/api/share/groups",
            headers=auth_header,
            json={"name": "Private Group", "description": "Members only"},
        )
        group_id = resp.json()["id"]

        join_resp = client.post(
            f"/api/share/groups/{group_id}/join",
            headers=second_auth_header,
        )
        assert join_resp.status_code == 200

        share_resp = client.post(
            f"/api/share/groups/{group_id}/files",
            headers=auth_header,
            json={"upload_id": test_upload},
        )
        assert share_resp.status_code == 200

        member_view = client.get("/api/share/shared-with-me", headers=second_auth_header)
        assert member_view.status_code == 200
        assert any(item["upload_id"] == test_upload and item["group_id"] == group_id for item in member_view.json())

        client.post(
            "/api/auth/register",
            json={"username": "outsider", "email": "outsider@example.com", "password": "password123"},
        )
        outsider_login = client.post(
            "/api/auth/login",
            data={"username": "outsider", "password": "password123"},
        )
        outsider_header = {"Authorization": f"Bearer {outsider_login.json()['access_token']}"}
        outsider_view = client.get("/api/share/shared-with-me", headers=outsider_header)
        assert outsider_view.status_code == 200
        assert all(item["upload_id"] != test_upload or item["group_id"] != group_id for item in outsider_view.json())


class TestComments:
    def test_comment_crud(self, client, auth_header, test_upload):
        create_resp = client.post(
            f"/api/share/{test_upload}/comments",
            headers=auth_header,
            json={"content": "Useful notes."},
        )
        assert create_resp.status_code == 200
        comment_id = create_resp.json()["id"]

        list_resp = client.get(f"/api/share/{test_upload}/comments", headers=auth_header)
        assert list_resp.status_code == 200
        assert any(comment["id"] == comment_id for comment in list_resp.json())

        delete_resp = client.delete(f"/api/share/comments/{comment_id}", headers=auth_header)
        assert delete_resp.status_code == 200
