"""Helpers for building model content blocks from job files."""
from __future__ import annotations

import base64
from pathlib import Path

MEDIA = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}


def image_block(path: Path) -> dict:
    data = base64.standard_b64encode(path.read_bytes()).decode()
    return {"type": "image", "source": {"type": "base64", "media_type": MEDIA[path.suffix.lower()], "data": data}}


def text_block(text: str) -> dict:
    return {"type": "text", "text": text}
