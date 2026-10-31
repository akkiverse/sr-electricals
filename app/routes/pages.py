"""Public pages (US-1 to US-4)."""

from __future__ import annotations

from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response

from app.adapters.store import get_store
from app.services.catalogue import filter_products
from app.web import render

router = APIRouter()


@router.get("/", include_in_schema=False)
def home(request: Request):
    cat = get_store().load()
    return render(
        request,
        "home.html",
        {
            "title": "Polycab, Havells and more electrical supplies in Deoghar | SR Electrical",
            "description": (
                f"{cat.settings.shop_name}, Tiwary Chowk, Deoghar: wires, cables, lighting, MCBs and "
                "switchgear for dealers, contractors and homes. Send your list on WhatsApp for a rate."
            ),
        },
        cat=cat,
    )


def _catalogue(request: Request, q: str, category: str, brand: str, heading: str, title: str, desc: str):
    cat = get_store().load()
    products = filter_products(cat, q=q, category=category, brand=brand)
    ctx = {
        "title": title,
        "description": desc,
        "heading": heading,
        "products": products,
        "q": q,
        "sel_category": category,
        "sel_brand": brand,
        "query_for": lambda **kw: _query(q, category, brand, **kw),
    }
    if request.headers.get("HX-Request") and request.headers.get("HX-Target") == "results":
        return render(request, "partials/results.html", ctx, cat=cat)
    return render(request, "products.html", ctx, cat=cat)


def _query(q_: str, category_: str, brand_: str, **change) -> str:
    params = {"q": q_, "category": category_, "brand": brand_}
    params.update(change)
    clean = {k: v for k, v in params.items() if v}
    return "/products" + (("?" + urlencode(clean)) if clean else "")


@router.get("/products", include_in_schema=False)
def products(request: Request, q: str = "", category: str = "", brand: str = ""):
    cat = get_store().load()
    bits = [x.name for x in (cat.brand(brand), cat.category(category)) if x]
    heading = " ".join(bits) if bits else "All products"
    if q:
        heading = f"Results for “{q}”" + (f" in {' '.join(bits)}" if bits else "")
    label = " ".join(bits) or "Electrical supplies"
    return _catalogue(
        request,
        q[:80],
        category,
        brand,
        heading,
        f"{label} in Deoghar: catalogue | SR Electrical",
        f"Browse {label.lower()} at SR Electrical, Deoghar. Search by brand and size, add to your quote list "
        "and send it on WhatsApp.",
    )


@router.get("/category/{slug}", include_in_schema=False)
def category_page(request: Request, slug: str, q: str = "", brand: str = ""):
    cat = get_store().load()
    c = cat.category(slug)
    if not c or not c.active:
        raise HTTPException(404)
    return _catalogue(
        request,
        q[:80],
        slug,
        brand,
        c.name,
        f"{c.name} in Deoghar | SR Electrical",
        f"{c.name} from Polycab, Havells, KEI, HPL, Anchor and more at SR Electrical, Deoghar. {c.description}",
    )


@router.get("/brand/{slug}", include_in_schema=False)
def brand_page(request: Request, slug: str, q: str = "", category: str = ""):
    cat = get_store().load()
    b = cat.brand(slug)
    if not b or not b.active:
        raise HTTPException(404)
    return _catalogue(
        request,
        q[:80],
        category,
        slug,
        f"{b.name} products",
        f"{b.name} dealer in Deoghar: wires, lights and switchgear | SR Electrical",
        f"{b.name} products at SR Electrical, Tiwary Chowk, Deoghar. Ask for bulk rates on WhatsApp.",
    )


@router.get("/products/{slug}", include_in_schema=False)
def product_page(request: Request, slug: str):
    cat = get_store().load()
    p = cat.product(slug)
    if not p or not cat.is_visible(p):
        raise HTTPException(404)
    brand, category = cat.brand(p.brand_slug), cat.category(p.category_slug)
    return render(
        request,
        "product.html",
        {
            "title": f"{p.name} in Deoghar | SR Electrical",
            "description": f"{p.name} ({brand.name}) at SR Electrical, Deoghar. "
            + ("Bulk quantities available. " if p.bulk_available else "")
            + "Add it to your quote list and get a rate on WhatsApp.",
            "p": p,
            "brand": brand,
            "category": category,
            "related": [x for x in cat.visible_products() if x.category_slug == p.category_slug and x.id != p.id][:4],
        },
        cat=cat,
    )


@router.get("/quote", include_in_schema=False)
def quote_page(request: Request):
    return render(
        request,
        "quote.html",
        {
            "title": "Your quote list | SR Electrical, Deoghar",
            "description": "Collect the items you need and send the list to SR Electrical, Deoghar on WhatsApp.",
        },
    )


@router.get("/img/{image_id}.webp", include_in_schema=False)
def image(image_id: str):
    if not image_id.isalnum() or len(image_id) > 40:
        raise HTTPException(404)
    data = get_store().get_image(image_id)
    if data is None:
        raise HTTPException(404)
    return Response(data, media_type="image/webp", headers={"Cache-Control": "public, max-age=31536000, immutable"})
