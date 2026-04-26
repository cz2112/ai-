"""Tests for upload endpoints: /api/uploads/*"""

import io
from unittest.mock import MagicMock, patch


class TestListUploads:
    """GET /api/uploads/"""

    def test_get_uploads_empty(self, client, auth_header):
        resp = client.get("/api/uploads/", headers=auth_header)
        assert resp.status_code == 200
        assert resp.json() == []


class TestCreateUpload:
    """POST /api/uploads/"""

    @patch("app.api.uploads.validate_file_magic", return_value=True)
    @patch("app.workers.tasks.process_upload")
    def test_upload_file(self, mock_task, mock_magic, client, auth_header, tmp_path):
        mock_task.delay = MagicMock()

        # Create a minimal PDF-like binary payload
        pdf_bytes = b"%PDF-1.4 fake content for testing"
        file = io.BytesIO(pdf_bytes)

        resp = client.post(
            "/api/uploads/",
            headers=auth_header,
            files={"file": ("lecture.pdf", file, "application/pdf")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["filename"] == "lecture.pdf"
        assert data["file_type"] == "pdf"
        assert data["status"] == "Pending"
        mock_task.delay.assert_called_once()


class TestStats:
    """GET /api/uploads/stats"""

    def test_get_stats(self, client, auth_header):
        resp = client.get("/api/uploads/stats", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()
        assert "total_uploads" in data
        assert "total_flashcards" in data
        assert data["total_uploads"] == 0


class TestQuota:
    """GET /api/uploads/quota"""

    def test_get_quota(self, client, auth_header):
        resp = client.get("/api/uploads/quota", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()
        assert "uploads_used" in data
        assert "uploads_limit" in data
        assert "max_file_size_mb" in data
        assert data["uploads_used"] == 0
        assert data["uploads_limit"] > 0


class TestSharedUploadAccess:
    def test_direct_share_user_can_view_detail_and_export(self, client, auth_header, second_auth_header, test_upload):
        user_resp = client.get("/api/auth/me", headers=second_auth_header)
        user2_id = user_resp.json()["id"]

        share_resp = client.post(
            "/api/share/",
            headers=auth_header,
            json={"upload_id": test_upload, "shared_with": user2_id},
        )
        assert share_resp.status_code == 200

        detail_resp = client.get(f"/api/uploads/{test_upload}", headers=second_auth_header)
        assert detail_resp.status_code == 200
        detail_data = detail_resp.json()
        assert detail_data["id"] == test_upload
        assert detail_data["user_id"] != user2_id

        export_resp = client.get(f"/api/uploads/{test_upload}/export", headers=second_auth_header)
        assert export_resp.status_code == 200
        assert "# test_notes.pdf" in export_resp.text
        assert "machine learning" in export_resp.text

    @patch("app.api.uploads.generate_knowledge_graph", return_value={"nodes": [{"id": "n1", "label": "ML", "group": "topic"}], "edges": []})
    def test_group_member_can_view_knowledge_graph(self, mock_graph, client, auth_header, second_auth_header, test_upload):
        group_resp = client.post(
            "/api/share/groups",
            headers=auth_header,
            json={"name": "Graph Group", "description": "Shared graphs"},
        )
        group_id = group_resp.json()["id"]

        join_resp = client.post(f"/api/share/groups/{group_id}/join", headers=second_auth_header)
        assert join_resp.status_code == 200

        share_resp = client.post(
            f"/api/share/groups/{group_id}/files",
            headers=auth_header,
            json={"upload_id": test_upload},
        )
        assert share_resp.status_code == 200

        graph_resp = client.get(f"/api/uploads/{test_upload}/knowledge-graph", headers=second_auth_header)
        assert graph_resp.status_code == 200
        assert graph_resp.json()["nodes"][0]["label"] == "ML"
        mock_graph.assert_called_once()

    def test_non_shared_user_cannot_view_upload_detail(self, client, auth_header, second_auth_header, test_upload):
        detail_resp = client.get(f"/api/uploads/{test_upload}", headers=second_auth_header)
        assert detail_resp.status_code == 404


class TestTags:
    """POST /api/uploads/tags  &  GET /api/uploads/tags/list"""

    def test_tag_crud(self, client, auth_header):
        # Initially no tags
        resp = client.get("/api/uploads/tags/list", headers=auth_header)
        assert resp.status_code == 200
        assert resp.json() == []

        # Create a tag
        resp = client.post(
            "/api/uploads/tags",
            headers=auth_header,
            json={"name": "physics"},
        )
        assert resp.status_code == 200
        tag = resp.json()
        assert tag["name"] == "physics"
        assert "id" in tag

        # List tags should now contain one entry
        resp = client.get("/api/uploads/tags/list", headers=auth_header)
        assert resp.status_code == 200
        tags = resp.json()
        assert len(tags) == 1
        assert tags[0]["name"] == "physics"
