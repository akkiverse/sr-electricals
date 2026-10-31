from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient

from app import studio_auth
from app.adapters.store import NO_DB_MESSAGE, MemoryStore, PostgresStore, SeedStore, get_store, set_store
from app.main import app
from app.services.images import to_webp
from tests.conftest import picture


def test_ac_5_1_admin_needs_owner_or_admin_signin(store, monkeypatch):
    """AC-5.1: Given the admin area /admin, when a visitor without a sign-in for this app with the owner or admin role opens it, then they are redirected to Studio sign-in; a signed-in owner or admin sees the admin dashboard."""
    client = TestClient(app)
    for path in ["/admin", "/admin/products", "/admin/settings", "/admin/export"]:
        r = client.get(path, follow_redirects=False)
        assert r.status_code == 302, path
        loc = urlparse(r.headers["location"])
        assert loc.netloc == "idea-studio-akkiverse.vercel.app" and loc.path == "/auth/login"
        q = parse_qs(loc.query)
        assert q["app"] == ["sr-electricals"] and q["code_challenge_method"] == ["S256"]
    assert client.post("/admin/settings", data={"tagline": "x"}, follow_redirects=False).status_code == 302
    # the public site stays open while the admin is closed
    assert client.get("/").status_code == 200
    # a signed-in person without a shop role is refused
    monkeypatch.setattr(
        studio_auth, "optional_user", lambda request: {"sub": "u2", "name": "Visitor", "email": "", "role": "user"}
    )
    r = client.get("/admin", follow_redirects=False)
    assert r.status_code == 403 and "owner role" in r.text
    for role in ("owner", "admin"):
        monkeypatch.setattr(
            studio_auth,
            "optional_user",
            lambda request, role=role: {"sub": "u1", "name": "Sanjay Singh", "email": "", "role": role},
        )
        r = client.get("/admin")
        assert r.status_code == 200 and "Shop admin" in r.text and "Signed in as Sanjay Singh" in r.text


def test_ac_5_1_previews_open_admin(store, monkeypatch):
    """AC-5.1 (previews): Vercel previews are private behind Vercel sign-in, so the admin opens there without Studio sign-in."""
    monkeypatch.setenv("VERCEL_ENV", "preview")
    assert TestClient(app).get("/admin").status_code == 200


def _product_form(**over):
    data = {"name": "Polycab LED bulb 12 W", "brand_slug": "polycab", "category_slug": "indoor-lighting",
            "specs": "Power: 12 W\nBase: B22", "price_inr": "149", "unit": "per piece", "active": "true",
            "bulk_available": "true", "best_selling": ""}  # fmt: skip
    data.update(over)
    return data


def test_ac_5_2_add_product_and_inline_errors(admin, store):
    """AC-5.2: Given the admin product form, when I submit a product with name, brand, category and optional specs, price, bulk flag, best-selling flag and image, then it is saved through the catalogue store and appears in the catalogue; missing required fields show inline errors."""
    r = admin.post(
        "/admin/products",
        data=_product_form(),
        files={"image": ("bulb.png", picture(), "image/png")},
        follow_redirects=False,
    )
    assert r.status_code == 303 and r.headers["location"] == "/admin/products?saved=product"
    p = store.load().product("polycab-led-bulb-12-w")
    assert p and p.specs == {"Power": "12 W", "Base": "B22"} and p.price_inr == 149 and p.bulk_available
    assert p.image.startswith("/img/") and p.image.endswith(".webp")
    page = admin.get("/products/polycab-led-bulb-12-w").text
    assert "<h1>Polycab LED bulb 12 W</h1>" in page and "₹149" in page
    assert "Polycab LED bulb 12 W" in admin.get("/products?category=indoor-lighting").text
    bad = admin.post("/admin/products", data=_product_form(name="", brand_slug="", category_slug="", price_inr="lots"))
    assert bad.status_code == 422
    for field in ("name", "brand_slug", "category_slug", "price_inr"):
        assert f'id="e-{field}"' in bad.text
    assert "Enter the product name" in bad.text and "Choose a brand." in bad.text


def test_ac_5_3_edit_and_deactivate(admin, store):
    """AC-5.3: Given the admin, when I edit or deactivate a product, then the change shows in the catalogue (deactivated products are hidden from visitors)."""
    p = store.load().product("havells-led-bulb-9-w")
    r = admin.post(
        f"/admin/products/{p.id}",
        data=_product_form(
            name="Havells LED bulb 9 W, pack of 10", brand_slug="havells", category_slug="indoor-lighting", price_inr=""
        ),
        follow_redirects=False,
    )
    assert r.status_code == 303
    html = admin.get("/products").text
    assert "Havells LED bulb 9 W, pack of 10" in html
    edited = store.load().product_by_id(p.id)
    assert admin.get(f"/products/{edited.slug}").status_code == 200
    admin.post(
        f"/admin/products/{p.id}",
        data=_product_form(name=edited.name, brand_slug="havells", category_slug="indoor-lighting", active=""),
    )
    assert "Havells LED bulb 9 W, pack of 10" not in admin.get("/products").text
    assert admin.get(f"/products/{edited.slug}").status_code == 404
    assert "Hidden" in admin.get("/admin/products").text


def test_ac_5_4_uploads_checked_and_shown(admin, store):
    """AC-5.4: Given the admin, when I upload an owner photo or product image (JPEG, PNG or WebP, at most 2 MB), then it is stored through the image store and shown on the site; other types or larger files are refused with a clear message."""
    r = admin.post(
        "/admin/owner-photo",
        files={"photo": ("me.jpg", picture("JPEG", (800, 800)), "image/jpeg")},
        follow_redirects=False,
    )
    assert r.status_code == 303
    url = store.load().settings.owner_photo
    assert url.startswith("/img/")
    assert f'src="{url}"' in admin.get("/").text
    img = admin.get(url)
    assert img.status_code == 200 and img.headers["content-type"] == "image/webp"
    gif = admin.post("/admin/owner-photo", files={"photo": ("a.gif", picture("GIF", (10, 10)), "image/gif")})
    assert gif.status_code == 422 and "Please choose a JPEG, PNG or WebP picture." in gif.text
    txt = admin.post("/admin/owner-photo", files={"photo": ("a.txt", b"hello", "text/plain")})
    assert txt.status_code == 422 and "JPEG, PNG or WebP" in txt.text
    big = admin.post(
        "/admin/owner-photo", files={"photo": ("big.png", b"\x89PNG" + b"0" * (2 * 1024 * 1024 + 10), "image/png")}
    )
    assert big.status_code == 422 and "larger than 2 MB" in big.text
    p = store.load().products[0]
    bad = admin.post(
        f"/admin/products/{p.id}",
        data=_product_form(),
        files={"image": ("x.gif", picture("GIF", (10, 10)), "image/gif")},
    )
    assert bad.status_code == 422 and 'id="e-image"' in bad.text


def test_ac_5_5_settings_change_public_pages(admin, store):
    """AC-5.5: Given the admin, when I edit shop settings (tagline, phone, WhatsApp number, hours, story, brands list, best-selling categories), then the public pages use the new values."""
    r = admin.post("/admin/settings", data={
        "tagline": "Deoghar's wire and lighting shop", "owner_name": "Sanjay Singh", "phone": "+91 98765 43210",
        "whatsapp": "9123456780", "open_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        "opens": "09:00", "closes": "20:30", "story": "New story for the shop.",
    }, follow_redirects=False)  # fmt: skip
    assert r.status_code == 303
    html = admin.get("/").text
    assert "Deoghar&#39;s wire and lighting shop" in html
    assert 'href="tel:+919876543210"' in html and 'href="https://wa.me/919123456780"' in html
    assert "Monday to Sunday, 9 AM to 8:30 PM" in html and "New story for the shop." in html
    out = admin.post("/api/whatsapp-link", json={"items": [{"name": "Wire", "qty": 1}]}).json()
    assert out["url"].startswith("https://wa.me/919123456780?text=")
    bad = admin.post(
        "/admin/settings",
        data={"tagline": "", "owner_name": "S", "phone": "123", "whatsapp": "", "opens": "9", "closes": "08:00"},
    )
    assert bad.status_code == 422
    for f in ("tagline", "phone", "whatsapp", "open_days", "opens"):
        assert f'id="e-{f}"' in bad.text
    # brands list and best-selling categories are edited from their own admin lists
    admin.post("/admin/brands", data={"name": "Finolex", "active": "true"})
    admin.post(
        "/admin/categories/outdoor-lighting", data={"name": "Outdoor lighting", "active": "true", "best_selling": ""}
    )
    html = admin.get("/").text
    assert ">Finolex</a>" in html.split("data-brands")[1].split("</ul>")[0]
    assert "/category/outdoor-lighting" not in html.split("data-best-categories")[1].split("</ul>")[0]


def test_ac_5_6_saves_need_the_database(seed_store):
    """AC-5.6: Given no database is connected, saves are refused with the message: Saving needs the shop database. Ask the founder to connect it. (With a database, saves go to Postgres; tests run against the in-memory store.)"""
    app.dependency_overrides[__import__("app.admin_auth", fromlist=["require_admin"]).require_admin] = lambda: {
        "name": "Owner",
        "role": "owner",
    }
    try:
        c = TestClient(app)
        assert NO_DB_MESSAGE in c.get("/admin").text
        before = SeedStore().load().model_dump_json()
        r = c.post("/admin/products", data=_product_form())
        assert r.status_code == 503 and NO_DB_MESSAGE in r.text
        r = c.post(
            "/admin/settings",
            data={
                "tagline": "x",
                "owner_name": "S",
                "phone": "9304359146",
                "whatsapp": "9304359146",
                "open_days": ["Monday"],
                "opens": "10:00",
                "closes": "18:00",
            },
        )
        assert r.status_code == 503 and NO_DB_MESSAGE in r.text
        assert c.post("/admin/brands/kei/remove").status_code == 503
        assert c.post("/admin/owner-photo", files={"photo": ("a.png", picture(), "image/png")}).status_code == 503
        assert SeedStore().load().model_dump_json() == before
    finally:
        app.dependency_overrides.clear()


def test_ac_5_6_store_choice_and_webp_resize(monkeypatch):
    """AC-5.6: With DATABASE_URL set the Postgres store is used; uploaded images are resized to WebP at most 1600 px wide."""
    set_store(None)
    monkeypatch.setenv("DATABASE_URL", "postgresql://user@localhost/none")
    assert isinstance(get_store(), PostgresStore)
    set_store(None)
    monkeypatch.delenv("DATABASE_URL")
    monkeypatch.setenv("POSTGRES_URL", "postgresql://user@localhost/none")
    assert isinstance(get_store(), PostgresStore)
    set_store(None)
    monkeypatch.delenv("POSTGRES_URL")
    monkeypatch.delenv("SR_STORE", raising=False)
    assert isinstance(get_store(), SeedStore)
    set_store(None)
    import io

    from PIL import Image

    out = Image.open(io.BytesIO(to_webp(picture("PNG", (3200, 1600)))))
    assert out.format == "WEBP" and out.width == 1600 and out.height == 800
    small = Image.open(io.BytesIO(to_webp(picture("JPEG", (640, 480)))))
    assert small.format == "WEBP" and small.width == 640


def test_ac_5_7_lists_with_edit_remove_and_confirmation(admin, store):
    """AC-5.7: Given the admin, when I open Brands, Categories or Products, then each shows a list of every item currently on the site (name, picture, shown or hidden) with Edit and Remove buttons and an Add button; Remove asks for confirmation, and after confirming the item no longer appears on any public page."""
    cat = store.load()
    for path, items in [
        ("/admin/brands", cat.brands),
        ("/admin/categories", cat.categories),
        ("/admin/products", cat.products),
    ]:
        html = admin.get(path).text
        assert "Add a" in html
        assert html.count('class="arow"') == len(items)
        assert html.count(" Edit</a>") == len(items) and html.count(" Remove</a>") == len(items)
        assert "Shown" in html
    html = admin.get("/admin/categories").text
    assert 'src="/static/img/cat-wires-and-cables.svg"' in html
    p = cat.product("anchor-bell-push-switch")
    confirm = admin.get(f"/admin/products/{p.id}/remove").text
    assert "Remove <strong>Anchor bell push switch</strong>" in confirm and "Yes, remove it" in confirm
    assert store.load().product(p.slug) is not None  # nothing removed until confirmed
    admin.post(f"/admin/products/{p.id}/remove")
    assert admin.get(f"/products/{p.slug}").status_code == 404
    assert "Anchor bell push switch" not in admin.get("/products?q=bell").text
    warn = admin.get("/admin/brands/benlo/remove").text
    assert "products use this brand" in warn
    admin.post("/admin/brands/benlo/remove")
    assert "/brand/benlo" not in admin.get("/").text
    assert admin.get("/brand/benlo").status_code == 404
    assert "Benlo" not in admin.get("/products").text.split('id="results"')[1]
    admin.post("/admin/categories/outdoor-lighting/remove")
    assert "Outdoor lighting" not in admin.get("/").text.split("data-best-categories")[1].split("</ul>")[0]
    assert admin.get("/category/outdoor-lighting").status_code == 404


def test_ac_5_8_brand_order_and_best_selling_on_home(admin, store):
    """AC-5.8: Given the admin, when I add, remove or reorder a brand or mark a category or product as best-selling, then the home page Brands we deal in and Best-selling sections show exactly the new list in the new order."""
    import re

    def brands():
        sec = admin.get("/").text.split("data-brands")[1].split("</ul>")[0]
        return re.findall(r'href="/brand/([a-z0-9-]+)"', sec)

    admin.post("/admin/brands/havells/move", data={"direction": "up"})
    assert brands() == ["polycab", "kei", "hpl", "benlo", "havells", "anchor"]
    admin.post("/admin/brands/polycab/move", data={"direction": "down"})
    assert brands() == ["kei", "polycab", "hpl", "benlo", "havells", "anchor"]
    admin.post("/admin/brands", data={"name": "Finolex", "active": "true"})
    admin.post("/admin/brands/hpl/remove")
    assert brands() == ["kei", "polycab", "benlo", "havells", "anchor", "finolex"]
    admin.post("/admin/brands/finolex", data={"name": "Finolex", "active": ""})
    assert "finolex" not in brands()

    def best_products():
        html = admin.get("/").text
        if "data-best-products" not in html:
            return []
        return re.findall(r'href="/products/([a-z0-9-]+)"', html.split("data-best-products")[1].split("</ul>")[0])

    before = best_products()
    p = store.load().product("hpl-rccb-40-a-30-ma")
    p_brand_back = admin.post("/admin/brands", data={"name": "HPL", "active": "true"}, follow_redirects=False)
    assert p_brand_back.status_code == 303
    admin.post(
        f"/admin/products/{p.id}",
        data=_product_form(name=p.name, brand_slug="hpl", category_slug=p.category_slug, best_selling="true"),
    )
    after = best_products()
    assert set(after) - set(before) == {"hpl-rccb-40-a-30-ma"}
    admin.post("/admin/categories/indoor-lighting/move", data={"direction": "up"})
    sec = admin.get("/").text.split("data-best-categories")[1].split("</ul>")[0]
    assert re.findall(r'href="/category/([a-z-]+)"', sec)[:2] == ["indoor-lighting", "wires-and-cables"]


def test_admin_export_backup(admin, store):
    r = admin.get("/admin/export")
    assert r.status_code == 200 and "attachment" in r.headers["content-disposition"]
    assert len(r.json()["products"]) == len(store.load().products)


def test_saved_data_from_this_version_loads(tmp_path):
    """Compatibility: a catalogue saved by v0.1.0 (data_version 1) loads unchanged."""
    s = MemoryStore()
    saved = s.load().model_dump_json()
    s2 = MemoryStore()
    s2._json = saved
    assert s2.load().model_dump_json() == saved
