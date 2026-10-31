import json
import re


def ld(html: str) -> dict:
    return json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S).group(1))


def test_ac_4_1_owner_with_photo_or_initials(client, store):
    """AC-4.1: Given the About section, when it loads, then it shows the owner name "Sanjay Singh", the owner photo if one is set (otherwise a neutral placeholder with initials), and the short shop story."""
    html = client.get("/").text
    about = html.split('id="about"', 1)[1].split("</section>", 1)[0]
    assert "Sanjay Singh" in about
    assert 'class="owner-photo owner-initials" role="img" aria-label="Sanjay Singh">SS<' in about
    assert store.load().settings.story[:40] in about
    cat = store.load()
    cat.settings.owner_photo = "/img/abc123.webp"
    store.save(cat)
    about = client.get("/").text.split('id="about"', 1)[1]
    assert '<img class="owner-photo" src="/img/abc123.webp" alt="Sanjay Singh, owner of SR Electrical"' in about


def test_ac_4_2_visit_us_address_hours_map_directions(client):
    """AC-4.2: Given the Visit us section, when it loads, then it shows the full address, the opening hours (seed: Monday to Saturday, 10:30 AM to 7 PM), an embedded map, and a Get directions link to Google Maps for that address; the LocalBusiness data carries the same hours."""
    html = client.get("/").text
    visit = html.split('id="visit"', 1)[1].split("</section>", 1)[0]
    assert "SR Electrical, Tiwary Chowk, Deoghar College Road, Deoghar, Jharkhand 814112, India" in visit
    assert "Monday to Saturday, 10:30 AM to 7 PM" in visit
    assert '<iframe title="Map showing SR Electrical, Deoghar" src="https://www.google.com/maps?q=' in visit
    assert 'href="https://www.google.com/maps/dir/?api=1&amp;destination=SR%20Electrical%2C%20Tiwary%20Chowk' in visit
    assert "Get directions" in visit
    spec = ld(html)["openingHoursSpecification"][0]
    assert spec["opens"] == "10:30" and spec["closes"] == "19:00"
    assert [d.rsplit("/", 1)[1] for d in spec["dayOfWeek"]] == [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
    ]
    assert ld(html)["openingHours"] == "Mo,Tu,We,Th,Fr,Sa 10:30-19:00"


def test_ac_4_3_footer_and_local_business_on_every_page(client):
    """AC-4.3: Given any page, when it loads, then the footer shows the address, phone and WhatsApp links, and the page contains LocalBusiness structured data (JSON-LD) with name, address and phone."""
    for path in [
        "/",
        "/products",
        "/products/kei-hr-fr-house-wire-1-5-sq-mm",
        "/quote",
        "/category/indoor-lighting",
        "/brand/havells",
        "/nope",
    ]:
        html = client.get(path).text
        footer = html.split('<footer class="footer">', 1)[1]
        assert "Tiwary Chowk, Deoghar College Road" in footer, path
        assert 'href="tel:+919304359146"' in footer and 'href="https://wa.me/919304359146"' in footer, path
        data = ld(html)
        assert data["@type"] == "LocalBusiness" and data["name"] == "SR Electrical"
        assert data["telephone"] == "+919304359146"
        assert data["address"]["addressLocality"] == "Deoghar" and data["address"]["postalCode"] == "814112"
