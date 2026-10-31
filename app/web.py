"""Template rendering helpers shared by the page routes."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import Request
from fastapi.templating import Jinja2Templates
from markupsafe import Markup

from app.models import BUYER_TYPES, Catalogue
from app.services.catalogue import image_for

HUB_URL = "https://idea-studio-akkiverse.vercel.app"
SITE_URL = "https://sr-electricals-akkiverse.vercel.app"
DAY_CODES = {
    "Monday": "Mo", "Tuesday": "Tu", "Wednesday": "We", "Thursday": "Th",
    "Friday": "Fr", "Saturday": "Sa", "Sunday": "Su",
}  # fmt: skip

templates = Jinja2Templates(directory=Path(__file__).resolve().parent / "templates")
templates.env.globals.update(HUB_URL=HUB_URL, SITE_URL=SITE_URL, BUYER_TYPES=BUYER_TYPES)


def inr(value: int | None) -> str:
    if value is None:
        return ""
    s = str(int(value))
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        s = ",".join(parts) + "," + tail
    return f"₹{s}"


templates.env.filters["inr"] = inr


def local_business(cat: Catalogue) -> Markup:
    s = cat.settings
    data = {
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "name": s.shop_name,
        "description": s.tagline,
        "url": SITE_URL,
        "telephone": f"+91{s.phone}",
        "address": {
            "@type": "PostalAddress",
            "streetAddress": s.street,
            "addressLocality": s.city,
            "addressRegion": s.region,
            "postalCode": s.postal_code,
            "addressCountry": "IN",
        },
        "openingHoursSpecification": [
            {
                "@type": "OpeningHoursSpecification",
                "dayOfWeek": [f"https://schema.org/{d}" for d in s.open_days],
                "opens": s.opens,
                "closes": s.closes,
            }
        ],
        "openingHours": f"{','.join(DAY_CODES[d] for d in s.open_days)} {s.opens}-{s.closes}",
        "founder": {"@type": "Person", "name": s.owner_name},
        "brand": [b.name for b in cat.shown_brands()],
    }
    text = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    return Markup(f'<script type="application/ld+json">{text}</script>')


def render(request: Request, name: str, context: dict | None = None, status_code: int = 200, cat=None):
    from app.adapters.store import get_store

    if cat is None:
        try:
            cat = get_store().load()
        except Exception:  # database down: still show the page shell with seed details
            from app.adapters.store import seed_catalogue

            cat = seed_catalogue()
    ctx = {
        "request": request,
        "path": request.url.path,
        "cat": cat,
        "s": cat.settings,
        "image_for": lambda p: image_for(cat, p),
        "local_business": local_business(cat),
    }
    ctx.update(context or {})
    resp = templates.TemplateResponse(request, name, ctx, status_code=status_code)
    resp.headers["Cache-Control"] = "no-cache"
    return resp
