import re


def test_ac_1_1_hero_with_call_and_whatsapp(client):
    """AC-1.1: Given the home page, when it loads, then it shows the shop name, a one-line tagline, and Call and WhatsApp buttons using the configured shop phone (seed 9304359146, linked as tel:+919304359146 and https://wa.me/919304359146)."""
    html = client.get("/").text
    assert "<h1>SR Electrical</h1>" in html
    assert 'class="hero-tag"' in html
    assert 'href="tel:+919304359146"' in html
    assert 'href="https://wa.me/919304359146"' in html


def test_ac_1_2_brands_section_links_to_filtered_catalogue(client):
    """AC-1.2: Given the configured brands (seed: Polycab, KEI, HPL, Benlo, Anchor, Havells), when the home page loads, then each brand appears in a "Brands we deal in" section, and each links to the catalogue filtered by that brand."""
    html = client.get("/").text
    assert "Brands we deal in" in html
    section = html.split("data-brands", 1)[1].split("</ul>", 1)[0]
    names = re.findall(r'href="/brand/([a-z-]+)"[^>]*><span class="stripe"[^>]*></span>([^<]+)</a>', section)
    assert [n for _, n in names] == ["Polycab", "KEI", "HPL", "Benlo", "Anchor", "Havells"]
    page = client.get("/brand/kei").text
    assert "KEI products" in page and "Havells" not in page.split('id="results"')[1].split("pgrid")[1].split("</ul>")[0]


def test_ac_1_3_best_selling_category_cards(client):
    """AC-1.3: Given the categories flagged best-selling, when the home page loads, then each shows as a card with name, image and link to its category page."""
    html = client.get("/").text
    section = html.split("data-best-categories", 1)[1].split("</ul>", 1)[0]
    for slug, name in [
        ("wires-and-cables", "Wires and cables"),
        ("indoor-lighting", "Indoor lighting"),
        ("outdoor-lighting", "Outdoor lighting"),
        ("mcbs-and-distribution-boards", "MCBs and distribution boards"),
        ("switches-and-switchgear", "Switches and switchgear"),
    ]:
        assert f'href="/category/{slug}"' in section
        assert f'<span class="ccard-name">{name}</span>' in section
        assert f'alt="{name}"' in section
        assert client.get(f"/category/{slug}").status_code == 200


def test_ac_1_4_who_we_serve(client):
    """AC-1.4: Given the home page, when it loads, then a "Who we serve" section lists Dealers, Contractors, Government contractors and Retail customers."""
    html = client.get("/").text
    section = html.split("Who we serve", 1)[1].split("</section>", 1)[0]
    for who in ["Dealers", "Contractors", "Government contractors", "Retail customers"]:
        assert f"<h3>{who}</h3>" in section
