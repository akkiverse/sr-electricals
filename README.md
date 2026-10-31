# SR Electricals

Wires, lighting, MCBs and switchgear from trusted brands in Deoghar, quoted on WhatsApp.

**Live:** https://sr-electricals-akkiverse.vercel.app (after the first release)
**Part of:** [Idea Studio by AkkiVerse](https://idea-studio-akkiverse.vercel.app)

## What it does

A fast, mobile-first shop website for SR Electrical, Tiwary Chowk, Deoghar. Visitors see the brands the shop deals in (Polycab, KEI, HPL, Benlo, Anchor, Havells), its best-selling categories, the owner and the shop's address, hours and map. They search and filter the catalogue, collect items with quantities in a quote list kept in their own browser, and send it to the shop on WhatsApp in one tap. The owner signs in with his Studio account and adds, edits and removes brands, categories and products, uploads photos and changes shop details.

## Status

| | |
|---|---|
| Stage | MVP built, waiting for release approval |
| Acceptance tests | 39 of 39 passing ([report](docs/quality/TEST-REPORT.md)) |
| Latest change | [CR-0001](docs/changes/CR-0001-mvp.md) First version (MVP) |

## Stack

Tier H: FastAPI renders Jinja2 pages with HTMX for live filtering; a little plain JavaScript keeps the quote list in the browser; Postgres (psycopg 3) stores the owner's edits once `DATABASE_URL` is set; Pillow turns uploads into WebP. See [ADR on the stack](docs/adr/0002-stack.md) and the studio's [stack policy](https://github.com/akkiverse/idea-studio/blob/main/STACK.md).

## Run it locally

```bash
uv sync
uv run uvicorn app.main:app --reload     # http://localhost:8000
uv run ruff check . && uv run ruff format --check .
uv run pytest
```

Without `DATABASE_URL` the site shows the seed catalogue in `app/data/catalogue.json` and the admin refuses saves. To try saving locally, set `DATABASE_URL` to a Postgres address in your terminal (never in a file), or set `SR_STORE=memory` for a throwaway in-memory store. Studio sign-in is off unless the founder turns it on for this app in the hub's `/admin/users`.

## How this repo is organised

This product is built with **spec-driven development**: the spec is the source of truth, every acceptance criterion has an automated test, and every change is recorded with its reason.

| Document | What it answers |
|---|---|
| [docs/product/BRIEF.md](docs/product/BRIEF.md) | Why this product exists, who pays, the business case |
| [docs/spec/SPEC.md](docs/spec/SPEC.md) | What it must do: user stories and acceptance criteria (`AC-x.y`) |
| [docs/architecture/ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md) | How it is built: components, data, integrations |
| [docs/adr/](docs/adr/) | Why each significant technical decision was made |
| [docs/changes/](docs/changes/) | Every change request: what changed, why, and its effect on the spec |
| [docs/design/DESIGN.md](docs/design/DESIGN.md) | Visual identity: palette, type, layout |
| [docs/plan/](docs/plan/) | The build plan and task list |
| [docs/quality/TEST-REPORT.md](docs/quality/TEST-REPORT.md) | Each acceptance criterion, its test, and the result |
| [CHANGELOG.md](CHANGELOG.md) | What changed in each release |
| [CONTRIBUTING.md](CONTRIBUTING.md) | How to make changes, by hand or through Idea Studio |

## Deployment

Hosted on Vercel (project `sr-electricals`). Every pull request gets a private preview; merging to `main` deploys to production at https://sr-electricals-akkiverse.vercel.app.
