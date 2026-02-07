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
