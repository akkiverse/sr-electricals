"""The WhatsApp quote message (AC-3.3). The same format is built in the browser by public/static/quote-core.js."""

from __future__ import annotations

from urllib.parse import quote

from pydantic import BaseModel, Field, field_validator

from app.models import BUYER_TYPES


class QuoteItem(BaseModel):
    slug: str = ""
    name: str = Field(min_length=1, max_length=200)
    brand: str = Field(default="", max_length=80)
    qty: int = Field(ge=1, le=9999)


class QuoteRequest(BaseModel):
    items: list[QuoteItem] = Field(min_length=1, max_length=200)
    name: str = Field(default="", max_length=80)
    buyer_type: str = ""

    @field_validator("buyer_type")
    @classmethod
    def _known_type(cls, v: str) -> str:
        if v and v not in BUYER_TYPES:
            raise ValueError("Choose Dealer, Contractor, Government contractor or Retail")
        return v


def quote_text(req: QuoteRequest, shop_name: str = "SR Electrical") -> str:
    lines = [f"Hello {shop_name}, please send your best rate for:"]
    for i, it in enumerate(req.items, 1):
        brand = f" ({it.brand})" if it.brand else ""
        lines.append(f"{i}. {it.name}{brand} x {it.qty}")
    if req.name.strip():
        lines.append(f"Name: {req.name.strip()}")
    if req.buyer_type:
        lines.append(f"I am a: {req.buyer_type}")
    lines.append("Sent from the SR Electrical website")
    return "\n".join(lines)


def whatsapp_link(number: str, text: str) -> str:
    return f"https://wa.me/{number}?text={quote(text, safe='')}"
