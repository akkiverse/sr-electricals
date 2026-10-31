"""Runs only when TEST_DATABASE_URL points at a throwaway Postgres (never the shop's database)."""

import os

import pytest

from app.adapters.store import PostgresStore, seed_catalogue

URL = os.environ.get("TEST_DATABASE_URL", "")
pytestmark = pytest.mark.skipif(not URL, reason="TEST_DATABASE_URL not set")


def test_ac_5_6_postgres_store_saves_and_seeds():
    """AC-5.6: Given the shop database is connected, when the owner saves a change, then it is stored in Postgres and the next load shows it."""
    import psycopg

    with psycopg.connect(URL, autocommit=True) as conn:
        conn.execute("DROP TABLE IF EXISTS sr_store, sr_images")
    store = PostgresStore(URL)
    cat = store.load()
    assert cat.model_dump() == seed_catalogue().model_dump()
    cat.settings.tagline = "Saved in Postgres"
    store.save(cat)
    assert PostgresStore(URL).load().settings.tagline == "Saved in Postgres"
    image_id = store.put_image(b"RIFF....WEBP")
    assert PostgresStore(URL).get_image(image_id) == b"RIFF....WEBP"
    assert store.get_image("missing") is None
