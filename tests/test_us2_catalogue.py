import re

from app.models import Product


def names(html: str) -> list[str]:
    return re.findall(r'<span class="pcard-name">([^<]+)</span>', html)


def test_ac_2_1_all_active_products_with_price_on_request(client, store):
    """AC-2.1: Given the catalogue page, when no filter is set, then all active products are listed with name, brand, category, image and a "Price on request" label unless the product has a price."""
    cat = store.load()
    cat.products[0].price_inr = 1450
    cat.products[1].active = False
    store.save(cat)
    html = client.get("/products").text
    listed = names(html)
    assert len(listed) == len(cat.products) - 1
    assert cat.products[1].name not in listed
    assert "₹1,450" in html
    assert html.count("Price on request") == len(listed) - 1
    first = html.split('<li class="pcard">')[1]
    assert 'class="pcard-brand"' in first and 'class="pcard-meta"' in first and "<img" in first


def test_ac_2_2_filter_by_category_and_brand_in_url(client):
    """AC-2.2: Given the catalogue, when I filter by a category and/or brand, then only matching products are shown and the filters appear in the URL query (shareable link)."""
    r = client.get("/products?category=wires-and-cables&brand=kei")
    listed = names(r.text)
    assert listed and all(n.startswith("KEI") for n in listed)
    assert all("wire" in n.lower() or "cable" in n.lower() for n in listed)
    assert 'hx-push-url="true"' in r.text and 'method="get"' in r.text
    assert "selected>KEI</option>" in r.text
    api = client.get("/api/products", params={"brand": "kei", "category": "wires-and-cables"}).json()
    assert {p["name"] for p in api} == set(listed)


def test_ac_2_3_search_case_insensitive_over_name_brand_category_specs(client, store):
    """AC-2.3: Given the catalogue, when I search for a term (for example "2.5 mm" or "polycab"), then only products whose name, brand, category or specs contain the term (case-insensitive) are shown."""
    listed = names(client.get("/products?q=POLYCAB").text)
    assert listed and all("Polycab" in n for n in listed)
    sizes = names(client.get("/products", params={"q": "2.5 mm"}).text)
    assert sizes and all("2.5" in n for n in sizes)
    by_spec = names(client.get("/products", params={"q": "ip66"}).text)
    assert by_spec and all(("street" in n.lower() or "flood" in n.lower()) for n in by_spec)
    by_cat = names(client.get("/products", params={"q": "switchgear"}).text)
    assert len(by_cat) == sum(1 for p in store.load().products if p.category_slug == "switches-and-switchgear")


def test_ac_2_4_no_matches_empty_state(client):
    """AC-2.4: Given a filter or search with no matches, when the page renders, then it shows "No products match" with a link to clear filters and a WhatsApp "Ask us" button."""
    html = client.get("/products?q=solar+inverter+xyz").text
    assert "No products match" in html
    assert 'href="/products"' in html and "Clear filters" in html
    assert "https://wa.me/919304359146?text=" in html and "Ask us" in html
    partial = client.get("/products?q=zzz", headers={"HX-Request": "true", "HX-Target": "results"}).text
    assert "No products match" in partial and "<html" not in partial


def test_ac_2_5_product_detail(client, store):
    """AC-2.5: Given a product, when I open its detail page, then it shows name, brand, category, specs (sizes, ratings), a "Bulk available" tag when set, and an "Add to quote" control with a quantity field."""
    p = store.load().product("polycab-fr-pvc-house-wire-2-5-sq-mm")
    html = client.get(f"/products/{p.slug}").text
    assert f"<h1>{p.name}</h1>" in html
    assert ">Polycab</a>" in html and "Wires and cables" in html
    assert '<th scope="row">Size</th><td>2.5 sq mm</td>' in html
    assert '<span class="tag">Bulk available</span>' in html
    assert "Add to quote" in html and 'name="qty"' in html and 'max="9999"' in html
    plain = next(x for x in store.load().products if not x.bulk_available)
    assert (
        '<span class="tag">Bulk available</span>'
        not in client.get(f"/products/{plain.slug}").text.split("product-tags")[1].split("</div>")[0]
    )
    missing = client.get("/products/not-a-real-thing")
    assert missing.status_code == 404 and "Page not found" in missing.text and 'href="/"' in missing.text


def test_search_ignores_hidden_brand_products(client, store):
    cat = store.load()
    cat.products.append(
        Product(id="x1", slug="ghost", name="Ghost wire", brand_slug="gone", category_slug="wires-and-cables")
    )
    store.save(cat)
    assert "Ghost wire" not in names(client.get("/products?q=ghost").text)
