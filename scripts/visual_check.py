"""Visual and phone-width check in a real browser (Playwright + Chromium).

Run the app first, for example:  SR_STORE=memory SR_ADMIN_OPEN=1 uv run uvicorn app.main:app --port 8011
Then:  python scripts/visual_check.py http://localhost:8011 /tmp/shots
Prints one line per check; exits non-zero if a 360 px check fails.
"""

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8011"
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else "/tmp/shots")
OUT.mkdir(parents=True, exist_ok=True)
PAGES = {
    "home": "/",
    "catalogue": "/products",
    "search-empty": "/products?q=solar+inverter",
    "product": "/products/polycab-fr-pvc-house-wire-2-5-sq-mm",
    "quote": "/quote",
    "admin": "/admin",
    "admin-products": "/admin/products",
    "admin-product-form": "/admin/products/p003",
    "admin-settings": "/admin/settings",
}
SMALL = """() => {
  const bad = [];
  document.querySelectorAll('a.btn, button, .chip, .pcard-add, .topnav a').forEach(el => {
    const r = el.getBoundingClientRect();
    if (r.width && r.height && r.height < 44 && getComputedStyle(el).visibility !== 'hidden') bad.push((el.textContent||el.getAttribute('aria-label')||'').trim().slice(0,30) + ':' + Math.round(r.height));
  });
  return {scroll: document.documentElement.scrollWidth, bad};
}"""
failed = False
with sync_playwright() as p:
    browser = p.chromium.launch()
    for scheme in ("light", "dark"):
        for width, height in ((375, 812), (1280, 900)):
            ctx = browser.new_context(
                viewport={"width": width, "height": height}, color_scheme=scheme, reduced_motion="reduce"
            )
            page = ctx.new_page()
            for name, path in PAGES.items():
                page.goto(BASE + path, wait_until="networkidle")
                page.screenshot(path=str(OUT / f"{name}-{width}-{scheme}.png"), full_page=True)
            ctx.close()
    ctx = browser.new_context(viewport={"width": 360, "height": 740})
    page = ctx.new_page()
    for name, path in PAGES.items():
        page.goto(BASE + path, wait_until="networkidle")
        res = page.evaluate(SMALL)
        ok = res["scroll"] <= 360 and not res["bad"]
        failed |= not ok and not name.startswith("admin")
        print(f"360px {name}: scrollWidth={res['scroll']} small_targets={res['bad']} {'OK' if ok else 'CHECK'}")
    # end-to-end quote flow
    page.goto(BASE + "/products/polycab-fr-pvc-house-wire-2-5-sq-mm")
    page.fill("#qty", "20")
    page.click("text=Add to quote")
    page.goto(BASE + "/products/havells-mcb-single-pole-16-a-c-curve")
    page.fill("#qty", "0")
    page.click("text=Add to quote")
    err = page.inner_text("#qty-error")
    page.fill("#qty", "12")
    page.click("text=Add to quote")
    page.goto(BASE + "/quote")
    page.reload()
    rows = page.locator(".qrow").count()
    count = page.inner_text("[data-quote-count]")
    page.fill("#buyer-name", "Ravi")
    page.select_option("#buyer-type", "Contractor")
    page.screenshot(path=str(OUT / "quote-filled-375.png"), full_page=True)
    urls = []
    page.on("request", lambda r: urls.append(r.url) if "wa.me" in r.url else None)
    page.click("text=Send on WhatsApp")
    page.wait_for_timeout(2500)
    print(f"quote flow: inline error={err!r} rows_after_reload={rows} badge={count} wa_url={urls[:1]}")
    # theme toggle remembered
    page.goto(BASE + "/")
    page.click("[data-theme-toggle]")
    page.reload()
    print("theme after toggle and reload:", page.evaluate("document.documentElement.dataset.theme"))
    browser.close()
sys.exit(1 if failed else 0)
