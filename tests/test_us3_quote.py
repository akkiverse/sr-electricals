from urllib.parse import parse_qs, urlparse

from app import studio_auth
from app.routes import api, pages


def test_ac_3_1_add_buttons_carry_item_details(client):
    """AC-3.1: Given a product, when I add it with quantity N, then the quote list count increases and the list shows the item with quantity N; adding it again increases its quantity. (Server side: every card and the product page carry the item for the browser quote list; the list logic is tested in tests/js/quote-core.test.js.)"""
    html = client.get("/products").text
    assert 'data-add-quote data-slug="polycab-fr-pvc-house-wire-2-5-sq-mm"' in html
    assert "data-quote-count" in html
    page = client.get("/products/polycab-fr-pvc-house-wire-2-5-sq-mm").text
    assert 'data-add-form data-slug="polycab-fr-pvc-house-wire-2-5-sq-mm"' in page and 'data-brand="Polycab"' in page


def test_ac_3_2_quantity_limits(client):
    """AC-3.2: Given the quote list, when I change a quantity or remove an item, then the list updates; quantities must be whole numbers from 1 to 9999, and invalid values show an inline error."""
    base = {"items": [{"slug": "a", "name": "Wire", "brand": "KEI", "qty": 1}]}
    for bad in (0, 10000, 2.5, "abc"):
        body = {"items": [dict(base["items"][0], qty=bad)]}
        r = client.post("/api/whatsapp-link", json=body)
        assert r.status_code == 422
        assert r.json()["error"]["message"] == "Quantities must be whole numbers from 1 to 9999."
    assert client.post("/api/whatsapp-link", json={"items": [dict(base["items"][0], qty=9999)]}).status_code == 200
    html = client.get("/quote").text
    assert 'min="1" max="9999"' in html and "data-remove" in html and 'data-f="error"' in html


def test_ac_3_3_whatsapp_message(client):
    """AC-3.3: Given a quote list with items and an optional name and "I am a" choice, when I press "Send on WhatsApp", then the browser opens a https://wa.me/<number>?text= link whose decoded text lists each item as "<name> (<brand>) x <qty>" plus the name and buyer type."""
    body = {
        "items": [
            {"slug": "w", "name": "Polycab FR PVC house wire 2.5 sq mm", "brand": "Polycab", "qty": 20},
            {"slug": "m", "name": "Havells MCB single pole 16 A, C curve", "brand": "Havells", "qty": 12},
        ],
        "name": "Ravi Kumar",
        "buyer_type": "Contractor",
    }
    out = client.post("/api/whatsapp-link", json=body).json()
    url = urlparse(out["url"])
    assert url.scheme == "https" and url.netloc == "wa.me" and url.path == "/919304359146"
    text = parse_qs(url.query)["text"][0]
    assert "Polycab FR PVC house wire 2.5 sq mm (Polycab) x 20" in text
    assert "Havells MCB single pole 16 A, C curve (Havells) x 12" in text
    assert "Name: Ravi Kumar" in text and "I am a: Contractor" in text
    html = client.get("/quote").text
    for t in ["Dealer", "Contractor", "Government contractor", "Retail"]:
        assert f'<option value="{t}">{t}</option>' in html
    assert "Send on WhatsApp" in html
    bad = client.post("/api/whatsapp-link", json=dict(body, buyer_type="Spy"))
    assert bad.status_code == 422


def test_ac_3_4_server_stores_no_quote_data(client, store):
    """AC-3.4: Given the quote list, when I reload the page, then it is still there (kept in the browser only); the server stores no quote or customer data."""
    before = store.load().model_dump_json()
    client.post("/api/whatsapp-link", json={"items": [{"slug": "a", "name": "Wire", "qty": 3}], "name": "Meena"})
    assert store.load().model_dump_json() == before
    assert "Meena" not in before
    public_posts = [
        r.path
        for router in (pages.router, api.router, studio_auth.router)
        for r in router.routes
        if "POST" in getattr(r, "methods", set())
    ]
    assert public_posts == ["/api/whatsapp-link"]
    assert "sr_quote_v1" in client.get("/static/quote-core.js").text


def test_ac_3_5_empty_list_state(client):
    """AC-3.5: Given an empty quote list, when I open it, then it says the list is empty and links to the catalogue; the send button is disabled."""
    html = client.get("/quote").text
    assert "Your quote list is empty" in html
    assert 'href="/products"' in html.split("data-quote-empty", 1)[1].split("</div>", 1)[0]
    assert "data-quote-send disabled" in html
