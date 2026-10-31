# ADR-0003: Catalogue as one JSON document in Postgres, read-only seed without a database

- **Status:** Accepted
- **Date:** 2026-10-31
- **Change request:** CR-0001

## Context
The owner must be able to change brands, categories, products, shop details and photos from the admin, and see the change on the next page load (AC-5.6). Vercel Functions keep nothing on disk between requests, so edits need a database. The founder is connecting a free Neon Postgres ("sr-electricals-master-db", Singapore) to the Vercel project; until then the site must still work. The catalogue is small (tens to a few hundred products) and edited by one person.

## Decision
- A `CatalogueStore` adapter (`app/adapters/store.py`) with three implementations:
  - **PostgresStore** when `DATABASE_URL` (or `POSTGRES_URL`, which the Vercel Neon integration also sets) is present. Table `sr_store` holds the whole catalogue as one `jsonb` row (key `catalogue`); table `sr_images` holds uploaded pictures as WebP bytes. Tables are created and seeded from `app/data/catalogue.json` on first use.
  - **SeedStore** when no database is connected: the seed catalogue, read-only. Admin saves are refused with "Saving needs the shop database. Ask the founder to connect it."
  - **MemoryStore** for tests and local trials (`SR_STORE=memory`).
- Uploaded images are checked (JPEG, PNG or WebP, at most 2 MB), resized to at most 1600 px wide, saved as WebP in `sr_images` and served from `/img/<id>.webp` with a one-year immutable cache.
- The app runs in Vercel region `sin1` (`vercel.json`), next to the database.
- Stored data carries `data_version` (1). Future shape changes add an upgrade step in `app/models.py:upgrade()`.

## Options considered
| Option | Pros | Cons |
|---|---|---|
| One JSON document (chosen) | Tiny code, atomic saves, keeps list order for free, easy JSON backup | Last save wins if two people edit at once (one owner, acceptable) |
| Normalised tables (settings, brands, categories, products) | Classic relational model | More code and migrations for a catalogue of this size |
| Vercel Blob for images | Purpose-built file storage | A separate service; the spec keeps images in the database to avoid it |

## Consequences
- No migration tool is needed yet; `upgrade()` handles future shapes when loading.
- The admin's **Download a backup (JSON)** gives the owner a full copy at any time.
- If two people edit at the same moment, the later save wins. Revisit if more editors are added.
