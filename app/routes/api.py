"""JSON API (spec section 8). Nothing here stores quote or customer data (AC-3.4)."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.adapters.store import get_store
from app.services.catalogue import filter_products, image_for
from app.services.quote import QuoteRequest, quote_text, whatsapp_link

router = APIRouter(prefix="/api")


class ProductOut(BaseModel):
    slug: str
    name: str
    brand: str
    category: str
    specs: dict[str, str]
    price_inr: int | None
    unit: str
    bulk_available: bool
    image: str
    url: str


class LinkOut(BaseModel):
    url: str
    text: str


@router.get("/products", response_model=list[ProductOut])
def products(q: str = "", category: str = "", brand: str = "") -> list[ProductOut]:
    cat = get_store().load()
    out = []
    for p in filter_products(cat, q=q[:80], category=category, brand=brand):
        b, c = cat.brand(p.brand_slug), cat.category(p.category_slug)
        out.append(
            ProductOut(
                slug=p.slug,
                name=p.name,
                brand=b.name if b else "",
                category=c.name if c else "",
                specs=p.specs,
                price_inr=p.price_inr,
                unit=p.unit,
                bulk_available=p.bulk_available,
                image=image_for(cat, p),
                url=f"/products/{p.slug}",
            )
        )
    return out


@router.post("/whatsapp-link", response_model=LinkOut)
def build_whatsapp_link(req: QuoteRequest) -> LinkOut:
    s = get_store().load().settings
    text = quote_text(req, s.shop_name)
    return LinkOut(url=whatsapp_link(s.wa_number, text), text=text)
