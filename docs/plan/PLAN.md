# SR Electricals: Build plan

For CR-0001 (MVP).

## Stack
Tier H (ADR-0002): FastAPI + Jinja2 + HTMX, a little plain JavaScript for the quote list and theme, Pillow for uploads, psycopg 3 for Postgres (ADR-0003). Studio sign-in kit for the admin (roles `owner`, `admin`). Hosted on Vercel project `sr-electricals`, region `sin1`.

## File layout
```
app/main.py               FastAPI app, error pages, /healthz
app/models.py             Settings, Brand, Category, Product, Catalogue (+ data_version upgrade)
app/adapters/store.py     PostgresStore, SeedStore, MemoryStore
app/services/             catalogue search, image checks (WebP), WhatsApp message
app/routes/pages.py       public pages and /img/<id>.webp
app/routes/api.py         /api/products, /api/whatsapp-link
app/routes/admin.py       owner admin
app/admin_auth.py         owner/admin role check on top of app/studio_auth.py (kit)
app/templates/            Jinja2 pages, partials, admin
app/data/catalogue.json   seed catalogue (6 brands, 5 categories, 38 products)
public/static/            CSS, JS (quote-core.js, app.js), htmx, fonts, SVG pictures
tests/                    pytest per story; tests/js for the quote list logic
scripts/visual_check.py   Playwright screenshots and 360 px checks
```

## How each user story is met
| Story | Approach | Files |
|---|---|---|
| US-1 Landing page | Server-rendered home from the catalogue settings, brands and best-selling categories and items | `home.html`, `pages.py` |
| US-2 Browse and search | Filter and word search over name, brand, category and specs; HTMX swaps the grid and pushes the URL | `services/catalogue.py`, `products.html`, `partials/results.html` |
| US-3 Quote list | Browser-only list in `localStorage`; pure logic in `quote-core.js`; `/api/whatsapp-link` builds the same message server side | `quote-core.js`, `app.js`, `quote.html`, `services/quote.py` |
| US-4 Owner and visit | About and Visit us sections, Google Maps embed and directions link, LocalBusiness JSON-LD on every page | `home.html`, `base.html`, `web.py` |
| US-5 Owner admin | Studio sign-in with owner/admin roles; lists with Edit, Remove (confirm page), move up/down; forms with inline errors; uploads to WebP; saves through the store | `routes/admin.py`, `admin/*.html`, `adapters/store.py` |
| US-6 Fast and clear | Mobile-first CSS tokens, designed dark theme, 44 px targets, small SVG pictures, self-hosted fonts | `app.css`, `base.html` |

## How existing users' data keeps working
First version, so there is no earlier data. From now on the stored catalogue carries `data_version`; any future shape change adds an upgrade step in `models.upgrade()` and a test that loads the older shape. Quote lists in browsers use the key `sr_quote_v1` and are validated on load.

## Risks and how they are handled
- **No database yet:** the site runs read-only on the seed catalogue; the admin says so plainly.
- **Owner role not yet assignable:** the hub needs `roles` in `registry/sr-electricals.json` (written at release). Until then the founder can use the default **App admin** role, which the admin accepts.
- **Seed catalogue is a starting guess:** products are typical items for these brands, labelled "Price on request"; the owner reviews and edits them.
- **Brand trademarks:** names only, no logos; a footer line says the names belong to their owners.
