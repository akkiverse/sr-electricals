"""CatalogueStore and ImageStore adapters (ADR-0003).

- PostgresStore: used when DATABASE_URL (or POSTGRES_URL) is set. One `sr_store` row holds the
  catalogue as JSON; `sr_images` holds uploaded pictures as WebP bytes. Seeded from the seed file
  on first start.
- SeedStore: read-only seed catalogue, used when no database is connected. Saves are refused.
- MemoryStore: writable, in memory; used by tests and for local trials (SR_STORE=memory).
"""

from __future__ import annotations

import json
import os
import secrets
from functools import lru_cache
from pathlib import Path
from typing import Protocol

from app.models import Catalogue, upgrade

SEED_FILE = Path(__file__).resolve().parent.parent / "data" / "catalogue.json"
NO_DB_MESSAGE = "Saving needs the shop database. Ask the founder to connect it."


class ReadOnlyStore(Exception):
    """Raised when a save is attempted without a database."""

    def __init__(self) -> None:
        super().__init__(NO_DB_MESSAGE)


@lru_cache(maxsize=1)
def _seed_text() -> str:
    return SEED_FILE.read_text(encoding="utf-8")


def seed_catalogue() -> Catalogue:
    return Catalogue.model_validate(upgrade(json.loads(_seed_text())))


class CatalogueStore(Protocol):
    writable: bool
    kind: str

    def load(self) -> Catalogue: ...
    def save(self, catalogue: Catalogue) -> None: ...
    def put_image(self, data: bytes) -> str: ...
    def get_image(self, image_id: str) -> bytes | None: ...


class SeedStore:
    writable = False
    kind = "seed"

    def load(self) -> Catalogue:
        return seed_catalogue()

    def save(self, catalogue: Catalogue) -> None:
        raise ReadOnlyStore()

    def put_image(self, data: bytes) -> str:
        raise ReadOnlyStore()

    def get_image(self, image_id: str) -> bytes | None:
        return None


class MemoryStore:
    writable = True
    kind = "memory"

    def __init__(self, catalogue: Catalogue | None = None) -> None:
        self._json = (catalogue or seed_catalogue()).model_dump_json()
        self.images: dict[str, bytes] = {}

    def load(self) -> Catalogue:
        return Catalogue.model_validate(upgrade(json.loads(self._json)))

    def save(self, catalogue: Catalogue) -> None:
        self._json = catalogue.model_dump_json()

    def put_image(self, data: bytes) -> str:
        image_id = secrets.token_hex(8)
        self.images[image_id] = data
        return image_id

    def get_image(self, image_id: str) -> bytes | None:
        return self.images.get(image_id)


class PostgresStore:
    writable = True
    kind = "postgres"

    def __init__(self, url: str) -> None:
        self.url = url
        self._ready = False

    def _connect(self):
        import psycopg  # imported here so the app starts without a database driver in use

        return psycopg.connect(self.url, connect_timeout=8, autocommit=True)

    def _ensure(self, conn) -> None:
        if self._ready:
            return
        conn.execute(
            "CREATE TABLE IF NOT EXISTS sr_store (key text PRIMARY KEY, data jsonb NOT NULL, "
            "updated_at timestamptz NOT NULL DEFAULT now())"
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS sr_images (id text PRIMARY KEY, data bytea NOT NULL, "
            "mime text NOT NULL DEFAULT 'image/webp', created_at timestamptz NOT NULL DEFAULT now())"
        )
        conn.execute(
            "INSERT INTO sr_store (key, data) VALUES ('catalogue', %s::jsonb) ON CONFLICT (key) DO NOTHING",
            (_seed_text(),),
        )
        self._ready = True

    def load(self) -> Catalogue:
        with self._connect() as conn:
            self._ensure(conn)
            row = conn.execute("SELECT data FROM sr_store WHERE key = 'catalogue'").fetchone()
        raw = row[0] if row else json.loads(_seed_text())
        return Catalogue.model_validate(upgrade(raw))

    def save(self, catalogue: Catalogue) -> None:
        with self._connect() as conn:
            self._ensure(conn)
            conn.execute(
                "INSERT INTO sr_store (key, data, updated_at) VALUES ('catalogue', %s::jsonb, now()) "
                "ON CONFLICT (key) DO UPDATE SET data = EXCLUDED.data, updated_at = now()",
                (catalogue.model_dump_json(),),
            )

    def put_image(self, data: bytes) -> str:
        image_id = secrets.token_hex(8)
        with self._connect() as conn:
            self._ensure(conn)
            conn.execute("INSERT INTO sr_images (id, data) VALUES (%s, %s)", (image_id, data))
        return image_id

    def get_image(self, image_id: str) -> bytes | None:
        with self._connect() as conn:
            self._ensure(conn)
            row = conn.execute("SELECT data FROM sr_images WHERE id = %s", (image_id,)).fetchone()
        return bytes(row[0]) if row else None


def database_url() -> str:
    return os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL") or ""


_store: CatalogueStore | None = None


def get_store() -> CatalogueStore:
    """The store for this process: Postgres if a database is connected, otherwise the read-only seed."""
    global _store
    if _store is None:
        url = database_url()
        if url:
            _store = PostgresStore(url)
        elif os.environ.get("SR_STORE") == "memory":
            _store = MemoryStore()
        else:
            _store = SeedStore()
    return _store


def set_store(store: CatalogueStore | None) -> None:
    """Tests use this to swap in a MemoryStore or SeedStore."""
    global _store
    _store = store
