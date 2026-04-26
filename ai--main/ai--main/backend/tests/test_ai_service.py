import base64

import httpx

from app.services import ai_service


def test_glm_layout_parsing_sends_png_as_data_url(tmp_path, monkeypatch):
    image_path = tmp_path / "ocr-test.png"
    image_bytes = b"fake-png-bytes"
    image_path.write_bytes(image_bytes)
    captured = {}

    def fake_post(url, headers, json, timeout):
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        return httpx.Response(
            200,
            json={"md_results": "recognized text"},
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(ai_service, "_get_glm_credentials", lambda: ("test-key", "https://glm.example"))
    monkeypatch.setattr(ai_service.httpx, "post", fake_post)

    text = ai_service._glm_layout_parsing(str(image_path))

    assert text == "recognized text"
    assert captured["url"] == "https://glm.example/layout_parsing"
    assert captured["headers"]["Authorization"] == "Bearer test-key"
    assert captured["json"]["model"] == ai_service.settings.GLM_OCR_MODEL
    assert captured["json"]["file"] == f"data:image/png;base64,{base64.b64encode(image_bytes).decode('ascii')}"


def test_glm_layout_parsing_sends_pdf_as_data_url_with_page_range(tmp_path, monkeypatch):
    pdf_path = tmp_path / "ocr-test.pdf"
    pdf_bytes = b"%PDF-1.4 fake pdf bytes"
    pdf_path.write_bytes(pdf_bytes)
    captured = {}

    def fake_post(url, headers, json, timeout):
        captured["json"] = json
        return httpx.Response(
            200,
            json={"md_results": ["page one", "page two"]},
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(ai_service, "_get_glm_credentials", lambda: ("test-key", "https://glm.example"))
    monkeypatch.setattr(ai_service.httpx, "post", fake_post)

    text = ai_service._glm_layout_parsing(str(pdf_path), start_page_id=1, end_page_id=2)

    assert text == "page one\n\npage two"
    assert captured["json"]["file"] == f"data:application/pdf;base64,{base64.b64encode(pdf_bytes).decode('ascii')}"
    assert captured["json"]["start_page_id"] == 1
    assert captured["json"]["end_page_id"] == 2
