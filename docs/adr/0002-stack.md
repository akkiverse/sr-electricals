# ADR-0002: Tier H (FastAPI + Jinja2 + HTMX) on Vercel

- **Status:** Accepted
- **Date:** 2026-10-31
- **Change request:** CR-0001

## Context
SR Electricals is mostly content pages (home, catalogue, product), simple filters, a browser-only quote list and a small owner admin with uploads. Visitors are mostly on budget phones on 4G, so pages must be light and fast. The studio's stack policy asks for Python on the back end.

## Decision
Use **tier H**: FastAPI renders Jinja2 templates on the server; HTMX swaps the product grid when filters or search change; a small amount of plain JavaScript keeps the quote list in the browser (`localStorage`) and drives the theme toggle. Static files are served from `public/` by Vercel's CDN. The admin uses the studio sign-in kit (`app/studio_auth.py`) with the app's own roles `owner` and `admin`.

## Options considered
| Option | Pros | Cons |
|---|---|---|
| Tier H (chosen) | Fast first paint on cheap phones, SEO-friendly HTML, all Python, small | Less app-like interactivity |
| Tier R (React or Vue + FastAPI) | Rich UI | Heavier bundle, slower first load, more code for a mostly static site |
| No back end | Simplest hosting | No owner admin, no sign-in, no database saves |

## Consequences
- Public pages are server-rendered per request, so owner edits show on the next load.
- The quote list is pure browser state; the server never stores customer data.
- Move up to tier R only if a real cart and checkout are added later.
