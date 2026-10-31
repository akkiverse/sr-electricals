"""Owner admin (US-5): brands, categories, products, shop settings and owner photo.

Every route needs a signed-in owner or admin (AC-5.1). Saves go through the catalogue store; without a
database they are refused with a clear message (AC-5.6).
"""

from __future__ import annotations

import json
import re

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import RedirectResponse, Response

from app.adapters.store import NO_DB_MESSAGE, ReadOnlyStore, get_store
from app.admin_auth import require_admin
from app.models import DAYS, Brand, Catalogue, Category, Product, now_iso, slugify
from app.services.images import ImageRejected, to_webp
from app.web import render

router = APIRouter(prefix="/admin", dependencies=[Depends(require_admin)])

PHONE_RE = re.compile(r"^(?:\+?91[\s-]?)?([6-9]\d{4})[\s-]?(\d{5})$")
TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


def _page(request: Request, name: str, ctx: dict, status: int = 200, cat: Catalogue | None = None):
    store = get_store()
    cat = cat or store.load()
    base = {
        "title": f"{ctx.get('heading', 'Shop admin')} | SR Electrical admin",
        "description": "Shop admin for SR Electrical, Deoghar.",
        "writable": store.writable,
        "no_db_message": NO_DB_MESSAGE,
        "user": getattr(request.state, "admin_user", None),
        "saved": request.query_params.get("saved", ""),
    }
    base.update(ctx)
    return render(request, name, base, status_code=status, cat=cat)


def _done(to: str, what: str) -> RedirectResponse:
    return RedirectResponse(f"{to}?saved={what}", status_code=303)


def _save(cat: Catalogue) -> None:
    get_store().save(cat)


async def _upload(file: UploadFile | None) -> str | None:
    """Return the stored image address, None when no file was chosen. Raises ImageRejected."""
    if file is None or not file.filename:
        return None
    data = await file.read(2 * 1024 * 1024 + 1)
    webp = to_webp(data)
    return f"/img/{get_store().put_image(webp)}.webp"


def _readonly(request: Request, template: str, ctx: dict):
    ctx = dict(ctx)
    ctx["form_error"] = NO_DB_MESSAGE
    return _page(request, template, ctx, status=503)


@router.get("", include_in_schema=False)
def dashboard(request: Request, user: dict = Depends(require_admin)):
    cat = get_store().load()
    counts = {
        "products": len(cat.products),
        "shown": len(cat.visible_products()),
        "brands": len(cat.brands),
        "categories": len(cat.categories),
    }
    return _page(request, "admin/dashboard.html", {"heading": "Shop admin", "counts": counts, "user": user}, cat=cat)


@router.get("/export", include_in_schema=False)
def export(request: Request):
    cat = get_store().load()
    body = json.dumps(cat.model_dump(), ensure_ascii=False, indent=1)
    return Response(
        body,
        media_type="application/json",
        headers={
            "Content-Disposition": 'attachment; filename="sr-electricals-catalogue.json"',
            "Cache-Control": "no-store",
        },
    )


# ---------------------------------------------------------------- products


def _product_form(request: Request, cat: Catalogue, p: Product | None, values: dict, errors: dict, status=200):
    return _page(
        request,
        "admin/product_form.html",
        {"heading": "Edit product" if p else "Add a product", "p": p, "v": values, "errors": errors},
        status=status,
        cat=cat,
    )


def _product_values(p: Product | None) -> dict:
    if not p:
        return {"name": "", "brand_slug": "", "category_slug": "", "specs": "", "price_inr": "", "unit": "",
                "bulk_available": False, "best_selling": False, "active": True}  # fmt: skip
    return {
        "name": p.name, "brand_slug": p.brand_slug, "category_slug": p.category_slug,
        "specs": "\n".join(f"{k}: {v}" for k, v in p.specs.items()),
        "price_inr": "" if p.price_inr is None else str(p.price_inr), "unit": p.unit,
        "bulk_available": p.bulk_available, "best_selling": p.best_selling, "active": p.active,
    }  # fmt: skip


def _parse_specs(text: str) -> tuple[dict[str, str], str | None]:
    specs: dict[str, str] = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        if ":" not in line:
            return (
                specs,
                f'Write each detail as "Name: value", for example "Size: 2.5 sq mm". Check: {line.strip()[:40]}',
            )
        k, v = line.split(":", 1)
        if k.strip() and v.strip():
            specs[k.strip()[:40]] = v.strip()[:120]
    return specs, None


@router.get("/products", include_in_schema=False)
def products_list(request: Request):
    return _page(request, "admin/products.html", {"heading": "Products"})


@router.get("/products/new", include_in_schema=False)
def product_new(request: Request):
    return _product_form(request, get_store().load(), None, _product_values(None), {})


@router.get("/products/{pid}", include_in_schema=False)
def product_edit(request: Request, pid: str):
    cat = get_store().load()
    p = cat.product_by_id(pid)
    if not p:
        raise HTTPException(404)
    return _product_form(request, cat, p, _product_values(p), {})


async def _product_submit(request: Request, pid: str | None, form: dict, image: UploadFile | None):
    store = get_store()
    cat = store.load()
    p = cat.product_by_id(pid) if pid else None
    if pid and not p:
        raise HTTPException(404)
    values = {
        "name": form["name"].strip(), "brand_slug": form["brand_slug"], "category_slug": form["category_slug"],
        "specs": form["specs"], "price_inr": form["price_inr"].strip(), "unit": form["unit"].strip(),
        "bulk_available": form["bulk_available"], "best_selling": form["best_selling"], "active": form["active"],
    }  # fmt: skip
    errors: dict[str, str] = {}
    if not values["name"]:
        errors["name"] = "Enter the product name, for example Polycab house wire 2.5 sq mm."
    if not cat.brand(values["brand_slug"]):
        errors["brand_slug"] = "Choose a brand."
    if not cat.category(values["category_slug"]):
        errors["category_slug"] = "Choose a category."
    specs, spec_error = _parse_specs(values["specs"])
    if spec_error:
        errors["specs"] = spec_error
    price = None
    if values["price_inr"]:
        digits = values["price_inr"].replace(",", "").replace("₹", "").strip()
        if not digits.isdigit() or not 0 < int(digits) < 10_000_000:
            errors["price_inr"] = "Enter the price in whole rupees, for example 1450, or leave it empty."
        else:
            price = int(digits)
    if errors:
        return _product_form(request, cat, p, values, errors, status=422)
    if not store.writable:
        return _page(
            request,
            "admin/product_form.html",
            {
                "heading": "Edit product" if p else "Add a product",
                "p": p,
                "v": values,
                "errors": {},
                "form_error": NO_DB_MESSAGE,
            },  # fmt: skip
            status=503,
            cat=cat,
        )
    try:
        new_image = await _upload(image)
    except ImageRejected as exc:
        return _product_form(request, cat, p, values, {"image": str(exc)}, status=422)
    if p is None:
        existing_ids = {x.id for x in cat.products}
        n = len(cat.products) + 1
        while f"p{n:03d}" in existing_ids:
            n += 1
        p = Product(
            id=f"p{n:03d}",
            slug=cat.unique_slug(values["name"], {x.slug for x in cat.products}),
            name=values["name"],
            brand_slug=values["brand_slug"],
            category_slug=values["category_slug"],
        )
        cat.products.insert(0, p)
    elif slugify(values["name"]) != slugify(p.name):
        p.slug = cat.unique_slug(values["name"], {x.slug for x in cat.products if x.id != p.id})
    p.name, p.brand_slug, p.category_slug = values["name"], values["brand_slug"], values["category_slug"]
    p.specs, p.price_inr, p.unit = specs, price, values["unit"][:60]
    p.bulk_available, p.best_selling, p.active = (
        values["bulk_available"],
        values["best_selling"],
        values["active"],
    )
    if new_image:
        p.image = new_image
    elif form.get("remove_image"):
        p.image = ""
    p.updated_at = now_iso()
    _save(cat)
    return _done("/admin/products", "product")


def _form_fields(
    name: str = Form(""),
    brand_slug: str = Form(""),
    category_slug: str = Form(""),
    specs: str = Form(""),
    price_inr: str = Form(""),
    unit: str = Form(""),
    bulk_available: bool = Form(False),
    best_selling: bool = Form(False),
    active: bool = Form(False),
    remove_image: bool = Form(False),
) -> dict:
    return {
        "name": name[:120], "brand_slug": brand_slug, "category_slug": category_slug, "specs": specs[:2000],
        "price_inr": price_inr[:12], "unit": unit, "bulk_available": bulk_available, "best_selling": best_selling,
        "active": active, "remove_image": remove_image,
    }  # fmt: skip


@router.post("/products", include_in_schema=False)
async def product_create(request: Request, form: dict = Depends(_form_fields), image: UploadFile | None = File(None)):
    return await _product_submit(request, None, form, image)


@router.post("/products/{pid}", include_in_schema=False)
async def product_update(
    request: Request, pid: str, form: dict = Depends(_form_fields), image: UploadFile | None = File(None)
):
    return await _product_submit(request, pid, form, image)


@router.get("/products/{pid}/remove", include_in_schema=False)
def product_remove_confirm(request: Request, pid: str):
    p = get_store().load().product_by_id(pid)
    if not p:
        raise HTTPException(404)
    return _page(
        request,
        "admin/confirm.html",
        {
            "heading": "Remove product",
            "thing": p.name,
            "action": f"/admin/products/{pid}/remove",
            "back": "/admin/products",
            "warning": "",
        },  # fmt: skip
    )


@router.post("/products/{pid}/remove", include_in_schema=False)
def product_remove(request: Request, pid: str):
    cat = get_store().load()
    if not cat.product_by_id(pid):
        raise HTTPException(404)
    cat.products = [x for x in cat.products if x.id != pid]
    try:
        _save(cat)
    except ReadOnlyStore:
        return _readonly(request, "admin/products.html", {"heading": "Products"})
    return _done("/admin/products", "removed")


# ---------------------------------------------------------------- settings and owner photo


def _settings_values(cat: Catalogue) -> dict:
    s = cat.settings
    return {"tagline": s.tagline, "phone": s.phone, "whatsapp": s.whatsapp, "open_days": list(s.open_days),
            "opens": s.opens, "closes": s.closes, "story": s.story, "owner_name": s.owner_name}  # fmt: skip


def _settings_page(request, cat, v, errors, status=200, form_error=""):
    return _page(
        request,
        "admin/settings.html",
        {"heading": "Shop details", "v": v, "errors": errors, "days": DAYS, "form_error": form_error},
        status=status,
        cat=cat,
    )


@router.get("/settings", include_in_schema=False)
def settings_page(request: Request):
    cat = get_store().load()
    return _settings_page(request, cat, _settings_values(cat), {})


def _phone(value: str) -> str | None:
    m = PHONE_RE.match(value.strip())
    return (m.group(1) + m.group(2)) if m else None


@router.post("/settings", include_in_schema=False)
async def settings_save(request: Request):
    form = await request.form()
    store = get_store()
    cat = store.load()
    v = {
        "tagline": str(form.get("tagline", "")).strip()[:160],
        "phone": str(form.get("phone", "")).strip(),
        "whatsapp": str(form.get("whatsapp", "")).strip(),
        "open_days": [d for d in form.getlist("open_days") if d in DAYS],
        "opens": str(form.get("opens", "")).strip(),
        "closes": str(form.get("closes", "")).strip(),
        "story": str(form.get("story", "")).strip()[:1200],
        "owner_name": str(form.get("owner_name", "")).strip()[:60],
    }
    errors = {}
    if not v["tagline"]:
        errors["tagline"] = "Enter a one-line tagline."
    if not v["owner_name"]:
        errors["owner_name"] = "Enter the owner's name."
    phone, wa = _phone(v["phone"]), _phone(v["whatsapp"])
    if not phone:
        errors["phone"] = "Enter a 10-digit mobile number, for example 9304359146."
    if not wa:
        errors["whatsapp"] = "Enter the 10-digit WhatsApp number, for example 9304359146."
    if not v["open_days"]:
        errors["open_days"] = "Tick at least one day the shop is open."
    if not TIME_RE.match(v["opens"]):
        errors["opens"] = "Enter the opening time, for example 10:30."
    if not TIME_RE.match(v["closes"]):
        errors["closes"] = "Enter the closing time, for example 19:00."
    elif not errors.get("opens") and v["closes"] <= v["opens"]:
        errors["closes"] = "Closing time must be after opening time."
    if errors:
        return _settings_page(request, cat, v, errors, status=422)
    if not store.writable:
        return _settings_page(request, cat, v, {}, status=503, form_error=NO_DB_MESSAGE)
    s = cat.settings
    s.tagline, s.phone, s.whatsapp, s.open_days = v["tagline"], phone, wa, v["open_days"]
    s.opens, s.closes, s.story, s.owner_name = v["opens"], v["closes"], v["story"], v["owner_name"]
    _save(cat)
    return _done("/admin/settings", "settings")


@router.post("/owner-photo", include_in_schema=False)
async def owner_photo(request: Request, photo: UploadFile | None = File(None), remove: bool = Form(False)):
    store = get_store()
    cat = store.load()
    if not store.writable:
        return _settings_page(request, cat, _settings_values(cat), {}, status=503, form_error=NO_DB_MESSAGE)
    if remove:
        cat.settings.owner_photo = ""
    else:
        try:
            url = await _upload(photo)
        except ImageRejected as exc:
            return _settings_page(request, cat, _settings_values(cat), {"photo": str(exc)}, status=422)
        if not url:
            return _settings_page(
                request,
                cat,
                _settings_values(cat),
                {"photo": "Please choose a picture to upload."},
                status=422,
            )
        cat.settings.owner_photo = url
    _save(cat)
    return _done("/admin/settings", "photo")


# ---------------------------------------------------------------- brands and categories

KINDS = {"brands": ("Brand", "brands"), "categories": ("Category", "categories")}


def _items(cat: Catalogue, kind: str) -> list:
    return cat.brands if kind == "brands" else cat.categories


def _kind(kind: str) -> str:
    if kind not in KINDS:
        raise HTTPException(404)
    return kind


@router.get("/{kind}", include_in_schema=False)
def group_list(request: Request, kind: str):
    kind = _kind(kind)
    cat = get_store().load()
    return _page(request, "admin/group.html", {"heading": kind.capitalize(), "kind": kind, "items": _items(cat, kind)})


def _group_form(request, kind, item, v, errors, status=200, cat=None, form_error=""):
    label = KINDS[kind][0]
    return _page(
        request,
        "admin/group_form.html",
        {
            "heading": f"Edit {label.lower()}" if item else f"Add a {label.lower()}",
            "kind": kind,
            "label": label,
            "item": item,
            "v": v,
            "errors": errors,
            "form_error": form_error,
        },  # fmt: skip
        status=status,
        cat=cat,
    )


def _group_values(item) -> dict:
    if item is None:
        return {"name": "", "description": "", "best_selling": False, "active": True}
    return {
        "name": item.name,
        "description": getattr(item, "description", ""),
        "best_selling": getattr(item, "best_selling", False),
        "active": item.active,
    }


@router.get("/{kind}/new", include_in_schema=False)
def group_new(request: Request, kind: str):
    kind = _kind(kind)
    return _group_form(request, kind, None, _group_values(None), {})


@router.get("/{kind}/{slug}", include_in_schema=False)
def group_edit(request: Request, kind: str, slug: str):
    kind = _kind(kind)
    cat = get_store().load()
    item = next((x for x in _items(cat, kind) if x.slug == slug), None)
    if not item:
        raise HTTPException(404)
    return _group_form(request, kind, item, _group_values(item), {}, cat=cat)


async def _group_submit(request, kind, slug, name, description, best_selling, active, remove_image, image):
    kind = _kind(kind)
    store = get_store()
    cat = store.load()
    items = _items(cat, kind)
    item = next((x for x in items if x.slug == slug), None) if slug else None
    if slug and not item:
        raise HTTPException(404)
    v = {"name": name.strip()[:60], "description": description.strip()[:300], "best_selling": best_selling,
         "active": active}  # fmt: skip
    errors = {}
    if not v["name"]:
        errors["name"] = f"Enter the {KINDS[kind][0].lower()} name."
    elif any(x.name.lower() == v["name"].lower() and x is not item for x in items):
        errors["name"] = f"There is already a {KINDS[kind][0].lower()} called {v['name']}."
    if errors:
        return _group_form(request, kind, item, v, errors, status=422, cat=cat)
    if not store.writable:
        return _group_form(request, kind, item, v, {}, status=503, cat=cat, form_error=NO_DB_MESSAGE)
    new_image = None
    if kind == "categories":
        try:
            new_image = await _upload(image)
        except ImageRejected as exc:
            return _group_form(request, kind, item, v, {"image": str(exc)}, status=422, cat=cat)
    if item is None:
        new_slug = cat.unique_slug(v["name"], {x.slug for x in items})
        item = Brand(slug=new_slug, name=v["name"]) if kind == "brands" else Category(slug=new_slug, name=v["name"])
        items.append(item)
    item.name, item.active = v["name"], v["active"]
    if isinstance(item, Category):
        item.description, item.best_selling = v["description"], v["best_selling"]
        if new_image:
            item.image = new_image
        elif remove_image:
            item.image = ""
    _save(cat)
    return _done(f"/admin/{kind}", KINDS[kind][0].lower())


@router.post("/{kind}", include_in_schema=False)
async def group_create(
    request: Request,
    kind: str,
    name: str = Form(""),
    description: str = Form(""),
    best_selling: bool = Form(False),
    active: bool = Form(False),
    remove_image: bool = Form(False),
    image: UploadFile | None = File(None),
):
    return await _group_submit(request, kind, None, name, description, best_selling, active, remove_image, image)


@router.post("/{kind}/{slug}", include_in_schema=False)
async def group_update(
    request: Request,
    kind: str,
    slug: str,
    name: str = Form(""),
    description: str = Form(""),
    best_selling: bool = Form(False),
    active: bool = Form(False),
    remove_image: bool = Form(False),
    image: UploadFile | None = File(None),
):
    return await _group_submit(request, kind, slug, name, description, best_selling, active, remove_image, image)


@router.post("/{kind}/{slug}/move", include_in_schema=False)
def group_move(request: Request, kind: str, slug: str, direction: str = Form("up")):
    kind = _kind(kind)
    cat = get_store().load()
    items = _items(cat, kind)
    i = next((n for n, x in enumerate(items) if x.slug == slug), None)
    if i is None:
        raise HTTPException(404)
    j = i - 1 if direction == "up" else i + 1
    if 0 <= j < len(items):
        items[i], items[j] = items[j], items[i]
    try:
        _save(cat)
    except ReadOnlyStore:
        return _readonly(request, "admin/group.html", {"heading": kind.capitalize(), "kind": kind, "items": items})
    return _done(f"/admin/{kind}", "order")


@router.get("/{kind}/{slug}/remove", include_in_schema=False)
def group_remove_confirm(request: Request, kind: str, slug: str):
    kind = _kind(kind)
    cat = get_store().load()
    item = next((x for x in _items(cat, kind) if x.slug == slug), None)
    if not item:
        raise HTTPException(404)
    field = "brand_slug" if kind == "brands" else "category_slug"
    used = sum(1 for p in cat.products if getattr(p, field) == slug)
    warning = (
        f"{used} product{'s use' if used != 1 else ' uses'} this {KINDS[kind][0].lower()}. "
        f"{'They' if used != 1 else 'It'} will be hidden from the site until you give "
        f"{'them' if used != 1 else 'it'} another {KINDS[kind][0].lower()}."
        if used
        else ""
    )
    return _page(
        request,
        "admin/confirm.html",
        {
            "heading": f"Remove {KINDS[kind][0].lower()}",
            "thing": item.name,
            "action": f"/admin/{kind}/{slug}/remove",
            "back": f"/admin/{kind}",
            "warning": warning,
        },  # fmt: skip
        cat=cat,
    )


@router.post("/{kind}/{slug}/remove", include_in_schema=False)
def group_remove(request: Request, kind: str, slug: str):
    kind = _kind(kind)
    cat = get_store().load()
    items = _items(cat, kind)
    if not any(x.slug == slug for x in items):
        raise HTTPException(404)
    items[:] = [x for x in items if x.slug != slug]
    try:
        _save(cat)
    except ReadOnlyStore:
        return _readonly(request, "admin/group.html", {"heading": kind.capitalize(), "kind": kind, "items": items})
    return _done(f"/admin/{kind}", "removed")
