"""The shop's data: settings, brands, categories and products (spec section "Data model")."""

from __future__ import annotations

import re
import unicodedata
from datetime import UTC, datetime

from pydantic import BaseModel, Field

DATA_VERSION = 1
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
BUYER_TYPES = ["Dealer", "Contractor", "Government contractor", "Retail"]


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text[:60] or "item"


def now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _clock(hhmm: str) -> str:
    """'10:30' -> '10:30 AM', '19:00' -> '7 PM'."""
    h, m = (int(x) for x in hhmm.split(":"))
    suffix = "AM" if h < 12 else "PM"
    h12 = h % 12 or 12
    return f"{h12}{f':{m:02d}' if m else ''} {suffix}"


class Settings(BaseModel):
    shop_name: str = "SR Electrical"
    tagline: str = "Wires, lighting, MCBs and switchgear from brands you trust, at dealer rates."
    owner_name: str = "Sanjay Singh"
    owner_photo: str = ""
    story: str = ""
    address: str = "SR Electrical, Tiwary Chowk, Deoghar College Road, Deoghar, Jharkhand 814112, India"
    street: str = "Tiwary Chowk, Deoghar College Road"
    city: str = "Deoghar"
    region: str = "Jharkhand"
    postal_code: str = "814112"
    map_query: str = "SR Electrical, Tiwary Chowk, Deoghar College Road, Deoghar, Jharkhand 814112"
    phone: str = "9304359146"
    whatsapp: str = "9304359146"
    open_days: list[str] = Field(default_factory=lambda: DAYS[:6])
    opens: str = "10:30"
    closes: str = "19:00"
    serves: list[str] = Field(
        default_factory=lambda: ["Dealers", "Contractors", "Government contractors", "Retail customers"]
    )

    @property
    def tel_link(self) -> str:
        return f"tel:+91{self.phone}"

    @property
    def phone_display(self) -> str:
        return f"+91 {self.phone[:5]} {self.phone[5:]}"

    @property
    def wa_number(self) -> str:
        return f"91{self.whatsapp}"

    @property
    def wa_link(self) -> str:
        return f"https://wa.me/{self.wa_number}"

    @property
    def days_text(self) -> str:
        idx = sorted(DAYS.index(d) for d in self.open_days if d in DAYS)
        if not idx:
            return "By appointment"
        if idx == list(range(idx[0], idx[-1] + 1)) and len(idx) > 2:
            return f"{DAYS[idx[0]]} to {DAYS[idx[-1]]}"
        return ", ".join(DAYS[i] for i in idx)

    @property
    def hours_text(self) -> str:
        return f"{self.days_text}, {_clock(self.opens)} to {_clock(self.closes)}"

    @property
    def owner_initials(self) -> str:
        return "".join(p[0] for p in self.owner_name.split()[:2]).upper() or "SR"


class Brand(BaseModel):
    slug: str
    name: str
    logo: str = ""  # only with the brand's written permission
    active: bool = True


class Category(BaseModel):
    slug: str
    name: str
    image: str = ""
    description: str = ""
    best_selling: bool = False
    active: bool = True


class Product(BaseModel):
    id: str
    slug: str
    name: str
    brand_slug: str
    category_slug: str
    specs: dict[str, str] = Field(default_factory=dict)
    price_inr: int | None = None
    unit: str = ""
    bulk_available: bool = False
    best_selling: bool = False
    image: str = ""
    active: bool = True
    updated_at: str = ""


class Catalogue(BaseModel):
    """Everything the public pages show. Lists are kept in display order."""

    data_version: int = DATA_VERSION
    settings: Settings = Field(default_factory=Settings)
    brands: list[Brand] = Field(default_factory=list)
    categories: list[Category] = Field(default_factory=list)
    products: list[Product] = Field(default_factory=list)

    # ----- lookups -----
    def brand(self, slug: str) -> Brand | None:
        return next((b for b in self.brands if b.slug == slug), None)

    def category(self, slug: str) -> Category | None:
        return next((c for c in self.categories if c.slug == slug), None)

    def product(self, slug: str) -> Product | None:
        return next((p for p in self.products if p.slug == slug), None)

    def product_by_id(self, pid: str) -> Product | None:
        return next((p for p in self.products if p.id == pid), None)

    # ----- what visitors see -----
    def shown_brands(self) -> list[Brand]:
        return [b for b in self.brands if b.active]

    def shown_categories(self) -> list[Category]:
        return [c for c in self.categories if c.active]

    def best_selling_categories(self) -> list[Category]:
        return [c for c in self.shown_categories() if c.best_selling]

    def is_visible(self, p: Product) -> bool:
        b, c = self.brand(p.brand_slug), self.category(p.category_slug)
        return p.active and b is not None and b.active and c is not None and c.active

    def visible_products(self) -> list[Product]:
        return [p for p in self.products if self.is_visible(p)]

    def best_selling_products(self) -> list[Product]:
        return [p for p in self.visible_products() if p.best_selling]

    def unique_slug(self, base: str, existing: set[str]) -> str:
        slug, n = slugify(base), 2
        candidate = slug
        while candidate in existing:
            candidate = f"{slug}-{n}"
            n += 1
        return candidate


def upgrade(raw: dict) -> dict:
    """Upgrade saved data from older shapes to the current DATA_VERSION (no older shapes yet)."""
    raw = dict(raw)
    raw.setdefault("data_version", DATA_VERSION)
    return raw
