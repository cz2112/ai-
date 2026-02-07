import re
import html


def sanitize_string(value: str, max_length: int = 500) -> str:
    """Strip HTML tags, escape special chars, enforce length."""
    value = value.strip()
    value = re.sub(r'<[^>]+>', '', value)
    value = html.escape(value)
    return value[:max_length]


def validate_username(v: str) -> str:
    v = v.strip()
    if not re.match(r'^[a-zA-Z0-9_]{3,50}$', v):
        raise ValueError('Username must be 3-50 alphanumeric characters or underscores')
    return v


def validate_email(v: str) -> str:
    v = v.strip().lower()
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
        raise ValueError('Invalid email format')
    if len(v) > 100:
        raise ValueError('Email too long')
    return v
