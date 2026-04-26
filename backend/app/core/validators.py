ALLOWED_MIME_TYPES = {
    "pdf": ["application/pdf"],
    "mp3": ["audio/mpeg", "audio/mp3"],
    "wav": ["audio/x-wav", "audio/wav"],
    "mp4": ["video/mp4"],
    "mov": ["video/quicktime"],
    "pptx": ["application/vnd.openxmlformats-officedocument.presentationml.presentation"],
    "ppt": ["application/vnd.ms-powerpoint"],
    "docx": ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"],
    "png": ["image/png"],
    "jpg": ["image/jpeg"],
    "jpeg": ["image/jpeg"],
}

# Magic byte signatures for common file types
MAGIC_SIGNATURES = {
    "pdf": [b"%PDF"],
    "mp3": [b"\xff\xfb", b"\xff\xf3", b"\xff\xf2", b"ID3"],
    "wav": [b"RIFF"],
    "mp4": [b"ftyp"],
    "mov": [b"ftyp"],
    "pptx": [b"PK\x03\x04"],
    "docx": [b"PK\x03\x04"],
    "ppt": [b"\xd0\xcf\x11\xe0"],
    "png": [b"\x89PNG"],
    "jpg": [b"\xff\xd8\xff"],
    "jpeg": [b"\xff\xd8\xff"],
}


def validate_file_magic(content: bytes, claimed_ext: str) -> bool:
    """Validate file content matches claimed extension using magic bytes."""
    signatures = MAGIC_SIGNATURES.get(claimed_ext)
    if not signatures:
        return False
    if claimed_ext in {"mp4", "mov"}:
        return len(content) >= 8 and content[4:8] == b"ftyp"
    header = content[:8]
    return any(header.startswith(sig) for sig in signatures)
