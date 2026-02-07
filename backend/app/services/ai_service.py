import json
from groq import Groq
from app.core.config import settings

client = Groq(api_key=settings.GROQ_API_KEY)

LLM_MODEL = "llama-3.3-70b-versatile"
STT_MODEL = "whisper-large-v3"


def transcribe_audio(file_path: str, language: str = "en") -> str:
    with open(file_path, "rb") as f:
        transcription = client.audio.transcriptions.create(
            file=(file_path, f),
            model=STT_MODEL,
            language=language,
            response_format="text",
        )
    return transcription


def extract_pdf_text(file_path: str) -> str:
    from PyPDF2 import PdfReader
    reader = PdfReader(file_path)
    text_parts = []
    for page in reader.pages:
        t = page.extract_text()
        if t:
            text_parts.append(t)
    return "\n".join(text_parts)


def extract_pptx_text(file_path: str) -> str:
    from pptx import Presentation
    prs = Presentation(file_path)
    text_parts = []
    for slide_num, slide in enumerate(prs.slides, 1):
        slide_texts = []
        for shape in slide.shapes:
            if shape.has_text_frame:
                for paragraph in shape.text_frame.paragraphs:
                    text = paragraph.text.strip()
                    if text:
                        slide_texts.append(text)
        if slide_texts:
            text_parts.append(f"[Slide {slide_num}]\n" + "\n".join(slide_texts))
    return "\n\n".join(text_parts)


def extract_docx_text(file_path: str) -> str:
    from docx import Document
    doc = Document(file_path)
    text_parts = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            text_parts.append(text)
    for table in doc.tables:
        for row in table.rows:
            row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
            if row_text:
                text_parts.append(row_text)
    return "\n".join(text_parts)


def extract_image_text(file_path: str) -> str:
    try:
        import pytesseract
        from PIL import Image
        image = Image.open(file_path)
        text = pytesseract.image_to_string(image)
        return text.strip()
    except Exception:
        return "[OCR processing failed or pytesseract not available]"


def detect_language(text: str) -> str:
    sample = text[:2000]
    prompt = (
        "Detect the primary language of the following text. "
        "Return ONLY the ISO 639-1 two-letter language code (e.g. 'en', 'zh', 'ja', 'ko', 'fr', 'de', 'es'). "
        "No extra text."
    )
    code = _chat(prompt, sample).strip().lower()[:2]
    return code if len(code) == 2 else "en"


def _strip_json_fences(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
    if raw.endswith("```"):
        raw = raw[:-3]
    return raw.strip()


def _chat(prompt: str, text: str) -> str:
    max_chars = 24000
    if len(text) > max_chars:
        text = text[:max_chars] + "\n...[truncated]"

    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": text},
        ],
        temperature=0.3,
        max_tokens=4096,
    )
    return response.choices[0].message.content


def _lang_instruction(lang: str) -> str:
    if lang == "zh":
        return "Respond in Chinese (中文). "
    elif lang == "ja":
        return "Respond in Japanese (日本語). "
    elif lang == "ko":
        return "Respond in Korean (한국어). "
    elif lang != "en":
        return f"Respond in the same language as the input material (language code: {lang}). "
    return ""


def generate_summary(text: str, lang: str = "en") -> str:
    prompt = (
        f"{_lang_instruction(lang)}"
        "You are a study assistant. Given the following study material, "
        "write a concise summary (200-400 words) that captures the main ideas, "
        "arguments, and conclusions. Use clear academic language."
    )
    return _chat(prompt, text)


def generate_key_concepts(text: str, lang: str = "en") -> list[dict]:
    prompt = (
        f"{_lang_instruction(lang)}"
        "You are a study assistant. Extract 5-10 key concepts from the following material. "
        "Return ONLY a JSON array where each element has 'title', 'description', and 'citation' fields. "
        "The 'citation' field should contain a short verbatim excerpt (1-2 sentences) from the original text "
        "that supports this concept. "
        "Example: [{\"title\": \"Concept\", \"description\": \"Explanation\", \"citation\": \"Original text excerpt...\"}]. "
        "No markdown, no extra text."
    )
    raw = _chat(prompt, text)
    return json.loads(_strip_json_fences(raw))


def generate_flashcards(text: str, lang: str = "en") -> list[dict]:
    prompt = (
        f"{_lang_instruction(lang)}"
        "You are a study assistant. Generate 8-15 Q&A flashcards from the following material "
        "to help a student self-test. Return ONLY a JSON array where each element has "
        "'question' and 'answer' fields. "
        "Example: [{\"question\": \"What is X?\", \"answer\": \"X is...\"}]. "
        "No markdown, no extra text."
    )
    raw = _chat(prompt, text)
    return json.loads(_strip_json_fences(raw))


# ── AI Chat (multi-turn Q&A) ────────────────────────────

def chat_with_context(messages: list[dict], context_text: str, lang: str = "en") -> str:
    """Multi-turn chat with document context."""
    system_prompt = (
        f"{_lang_instruction(lang)}"
        "You are a study assistant. Answer questions based on the following study material. "
        "If the answer is not in the material, say so clearly.\n\n"
        f"Study Material:\n{context_text[:20000]}"
    )
    all_messages = [{"role": "system", "content": system_prompt}] + messages
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=all_messages,
        temperature=0.4,
        max_tokens=2048,
    )
    return response.choices[0].message.content


# ── Knowledge Graph ──────────────────────────────────────

def generate_knowledge_graph(text: str, lang: str = "en") -> dict:
    prompt = (
        f"{_lang_instruction(lang)}"
        "Extract a knowledge graph from the following study material. "
        "Return ONLY a JSON object with 'nodes' and 'edges' arrays. "
        "Each node: {\"id\": \"unique_id\", \"label\": \"concept name\", \"group\": \"category\"}. "
        "Each edge: {\"source\": \"node_id\", \"target\": \"node_id\", \"label\": \"relationship\"}. "
        "Limit to 15-25 nodes. No markdown, no extra text."
    )
    raw = _chat(prompt, text)
    return json.loads(_strip_json_fences(raw))


# ── Learning Path ────────────────────────────────────────

def generate_learning_path(summaries: list[str], known_concepts: list[str], lang: str = "en") -> list[dict]:
    prompt = (
        f"{_lang_instruction(lang)}"
        "Based on the student's study materials and known concepts, "
        "suggest a learning path with 5-8 steps. "
        "Return ONLY a JSON array: [{\"step\": 1, \"topic\": \"...\", \"reason\": \"...\", \"resources\": \"...\"}]. "
        "No markdown."
    )
    combined = "Materials:\n" + "\n---\n".join(summaries[:5])
    combined += "\n\nKnown concepts:\n" + ", ".join(known_concepts[:30])
    raw = _chat(prompt, combined)
    return json.loads(_strip_json_fences(raw))
