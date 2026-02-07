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
