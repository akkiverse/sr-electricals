"""Search and filters for the catalogue (US-2)."""

from __future__ import annotations

from app.models import Catalogue, Product


def matches(cat: Catalogue, p: Product, term: str) -> bool:
    term = term.strip().lower()
    if not term:
        return True
    brand = cat.brand(p.brand_slug)
    category = cat.category(p.category_slug)
    haystack = " ".join(
        [p.name, brand.name if brand else "", category.name if category else "", p.unit]
        + [f"{k} {v}" for k, v in p.specs.items()]
    ).lower()
    # "2.5 mm" should find "2.5 sq mm": every word of the search must appear.
    return term in haystack or all(word in haystack for word in term.split())


def filter_products(cat: Catalogue, q: str = "", category: str = "", brand: str = "") -> list[Product]:
    return [
        p
        for p in cat.visible_products()
        if (not category or p.category_slug == category) and (not brand or p.brand_slug == brand) and matches(cat, p, q)
    ]


def image_for(cat: Catalogue, p: Product) -> str:
    if p.image:
        return p.image
    c = cat.category(p.category_slug)
    return c.image if c and c.image else "/static/img/cat-generic.svg"
