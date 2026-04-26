"""Tests for chat endpoints: /api/chat/*"""

from unittest.mock import patch


class TestChat:
    """POST /api/chat/{upload_id}  &  GET /api/chat/{upload_id}/conversations"""

    @patch("app.api.chat.chat_with_context", return_value="This is an AI response about ML.")
    def test_create_conversation(self, mock_ai, client, auth_header, test_upload):
        resp = client.post(
            f"/api/chat/{test_upload}",
            headers=auth_header,
            json={"message": "Explain machine learning"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["role"] == "assistant"
        assert "AI response" in data["content"]
        mock_ai.assert_called_once()

    @patch("app.api.chat.chat_with_context", return_value="AI reply")
    def test_list_conversations(self, mock_ai, client, auth_header, test_upload):
        # Create a conversation first
        client.post(
            f"/api/chat/{test_upload}",
            headers=auth_header,
            json={"message": "Hello AI"},
        )

        resp = client.get(
            f"/api/chat/{test_upload}/conversations",
            headers=auth_header,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["upload_id"] == test_upload
        assert "messages" in data[0]

    @patch("app.api.chat.chat_with_context", return_value="Shared user reply")
    def test_shared_user_can_chat_with_shared_upload(self, mock_ai, client, auth_header, second_auth_header, test_upload):
        user_resp = client.get("/api/auth/me", headers=second_auth_header)
        user2_id = user_resp.json()["id"]

        share_resp = client.post(
            "/api/share/",
            headers=auth_header,
            json={"upload_id": test_upload, "shared_with": user2_id},
        )
        assert share_resp.status_code == 200

        chat_resp = client.post(
            f"/api/chat/{test_upload}",
            headers=second_auth_header,
            json={"message": "What is this about?"},
        )
        assert chat_resp.status_code == 200
        assert chat_resp.json()["content"] == "Shared user reply"

        list_resp = client.get(
            f"/api/chat/{test_upload}/conversations",
            headers=second_auth_header,
        )
        assert list_resp.status_code == 200
        data = list_resp.json()
        assert len(data) == 1
        assert data[0]["upload_id"] == test_upload
        mock_ai.assert_called_once()
