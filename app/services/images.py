"""Checks and shrinks uploaded pictures (AC-5.4, AC-5.6): JPEG, PNG or WebP up to 2 MB, saved as WebP."""

from __future__ import annotations

import io

from PIL import Image, ImageOps, UnidentifiedImageError

MAX_BYTES = 2 * 1024 * 1024
MAX_WIDTH = 1600
ALLOWED = {"JPEG", "PNG", "WEBP"}
TYPE_MESSAGE = "Please choose a JPEG, PNG or WebP picture."
SIZE_MESSAGE = "That picture is larger than 2 MB. Please choose a smaller one or resize it."


class ImageRejected(ValueError):
    pass


def to_webp(data: bytes) -> bytes:
    if not data:
        raise ImageRejected("Please choose a picture to upload.")
    if len(data) > MAX_BYTES:
        raise ImageRejected(SIZE_MESSAGE)
    try:
        img = Image.open(io.BytesIO(data))
        fmt = img.format
        img.load()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise ImageRejected(TYPE_MESSAGE) from exc
    if fmt not in ALLOWED:
        raise ImageRejected(TYPE_MESSAGE)
    img = ImageOps.exif_transpose(img)
    if img.width > MAX_WIDTH:
        img = img.resize((MAX_WIDTH, round(img.height * MAX_WIDTH / img.width)), Image.LANCZOS)
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA" if "A" in img.getbands() else "RGB")
    out = io.BytesIO()
    img.save(out, "WEBP", quality=82, method=4)
    return out.getvalue()
