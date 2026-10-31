import re
from html.parser import HTMLParser
from pathlib import Path

CSS = (Path(__file__).resolve().parent.parent / "public" / "static" / "app.css").read_text()
PUBLIC = [
    "/",
    "/products",
    "/products?q=zzz",
    "/products/havells-led-bulb-9-w",
    "/quote",
    "/category/wires-and-cables",
    "/brand/polycab",
]


class A11y(HTMLParser):
    """A small automated accessibility check: labels on form controls, alt on images, names on buttons and links."""

    def __init__(self):
        super().__init__()
        self.labels_for, self.controls, self.problems, self.lang = set(), [], [], None
        self._button = None
        self._link = None
        self._label_depth = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "html":
            self.lang = a.get("lang")
        if tag == "label":
            self._label_depth += 1
            if a.get("for"):
                self.labels_for.add(a["for"])
        is_control = tag in ("input", "select", "textarea") and a.get("type") not in ("hidden", "submit")
        if is_control and not (a.get("aria-label") or self._label_depth):
            self.controls.append(a.get("id"))
        if tag == "img" and "alt" not in a:
            self.problems.append(f"img without alt: {a.get('src')}")
        if tag == "iframe" and not a.get("title"):
            self.problems.append("iframe without title")
        if tag == "button":
            self._button = {"label": a.get("aria-label"), "text": ""}
        if tag == "a" and "href" in a:
            self._link = {"label": a.get("aria-label"), "text": "", "href": a["href"]}

    def handle_data(self, data):
        if self._button is not None:
            self._button["text"] += data.strip()
        if self._link is not None:
            self._link["text"] += data.strip()

    def handle_endtag(self, tag):
        if tag == "label":
            self._label_depth -= 1
        if tag == "button" and self._button is not None:
            if not (self._button["label"] or self._button["text"]):
                self.problems.append("button without a name")
            self._button = None
        if tag == "a" and self._link is not None:
            if not (self._link["label"] or self._link["text"]):
                self.problems.append(f"link without a name: {self._link['href']}")
            self._link = None

    def report(self):
        missing = [c for c in self.controls if c not in self.labels_for]
        return self.problems + [f"form control without label: {c}" for c in missing]


def _vars(block: str) -> dict:
    return dict(re.findall(r"--([a-z-]+):\s*(#[0-9a-fA-F]{6})", block))


def _lum(hex_):
    rgb = [int(hex_[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contrast(a, b):
    la, lb = sorted([_lum(a), _lum(b)], reverse=True)
    return (la + 0.05) / (lb + 0.05)


def test_ac_6_1_phone_width_no_sideways_scroll_and_44px_targets(client):
    """AC-6.1: Given a 360 px wide screen, when any public page renders, then nothing scrolls sideways and all buttons are at least 44 px tall. (Checked here from the markup and CSS; checked in a real browser at 360 px by scripts/visual_check.py, see the test report.)"""
    for path in PUBLIC:
        assert '<meta name="viewport" content="width=device-width, initial-scale=1">' in client.get(path).text
    assert "overflow-x: hidden" in CSS.split("body {", 1)[1].split("}", 1)[0]
    for selector in [".btn {", ".btn.sm {", ".chip {", ".pcard-add {", ".topnav a {", ".footer-links a {", ".check {"]:
        rules = [part.split("}", 1)[0] for part in CSS.split(selector)[1:]]
        heights = [int(m.group(1)) for r in rules if (m := re.search(r"min-height:\s*(\d+)px", r))]
        assert heights and min(heights) >= 44, selector
    for selector in [".icon-btn {", ".theme-toggle {"]:
        rule = CSS.split(selector, 1)[1].split("}", 1)[0]
        assert int(re.search(r"height:\s*(\d+)px", rule).group(1)) >= 44, selector
    assert re.search(r"\.wrap \{ width: min\(1200px, 100% - 32px\)", CSS)


def test_ac_6_2_dark_theme_follows_system_and_toggle_is_remembered(client):
    """AC-6.2: Given the system theme is dark, when a page loads, then the dark theme is used; a toggle switches themes and the choice is remembered."""
    assert "@media (prefers-color-scheme: dark)" in CSS and ':root:not([data-theme="light"])' in CSS
    assert ':root[data-theme="dark"]' in CSS
    html = client.get("/").text
    assert "data-theme-toggle" in html and 'localStorage.getItem("sr_theme")' in html
    js = client.get("/static/app.js").text
    assert 'store.setItem("sr_theme", next)' in js


def test_ac_6_3_automated_accessibility_check(client):
    """AC-6.3: Given any public page, when checked with an automated accessibility check, then there are no critical issues (labels on inputs, alt text on images, contrast AA, visible focus)."""
    for path in PUBLIC:
        checker = A11y()
        checker.feed(client.get(path).text)
        assert checker.lang == "en-IN"
        assert checker.report() == [], (path, checker.report())
    light = _vars(CSS.split(":root {", 1)[1].split("}", 1)[0])
    dark = _vars(CSS.split(':root[data-theme="dark"] {', 1)[1].split("}", 1)[0])
    for theme in (light, dark):
        assert contrast(theme["ink"], theme["bg"]) >= 7
        assert contrast(theme["muted"], theme["bg"]) >= 4.5
        assert contrast(theme["muted"], theme["surface"]) >= 4.5
        assert contrast(theme["link"], theme["bg"]) >= 4.5
        assert contrast(theme["brand-ink"], theme["brand"]) >= 4.5
        assert contrast("#ffffff", theme["wa"]) >= 4.5
        assert contrast(theme["spark-ink"], theme["spark"]) >= 4.5
    assert ":focus-visible { outline: 3px solid var(--spark)" in CSS


def test_ac_6_4_unique_titles_and_descriptions_with_deoghar(client):
    """AC-6.4: Given each public page, when it renders, then it has a unique title and meta description including "Deoghar"."""
    titles, descs = [], []
    for path in [
        "/",
        "/products",
        "/products/havells-led-bulb-9-w",
        "/products/kei-hr-fr-house-wire-1-5-sq-mm",
        "/quote",
        "/category/wires-and-cables",
        "/category/indoor-lighting",
        "/brand/polycab",
        "/brand/kei",
    ]:
        html = client.get(path).text
        title = re.search(r"<title>(.*?)</title>", html).group(1)
        desc = re.search(r'<meta name="description" content="(.*?)">', html).group(1)
        assert "Deoghar" in title and "Deoghar" in desc, path
        titles.append(title)
        descs.append(desc)
    assert len(set(titles)) == len(titles) and len(set(descs)) == len(descs)
    assert "Polycab, Havells and more electrical supplies in Deoghar | SR Electrical" in titles
    home = client.get("/").text
    assert 'property="og:title"' in home and 'name="theme-color"' in home and 'rel="icon"' in home
    assert "Part of Idea Studio by AkkiVerse" in home
