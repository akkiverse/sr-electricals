import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app import studio_auth
from app.adapters.store import MemoryStore, SeedStore, set_store
from app.admin_auth import require_admin
from app.main import app

OWNER = {"sub": "u1", "name": "Sanjay Singh", "email": "owner@example.com", "role": "owner"}


@pytest.fixture(autouse=True)
def signin_off(monkeypatch):
    """Studio sign-in is off for this app unless a test turns it on. Never calls the real hub."""
    monkeypatch.setattr(studio_auth, "signin_required", lambda: False)
    monkeypatch.delenv("VERCEL_ENV", raising=False)
    monkeypatch.delenv("SR_ADMIN_OPEN", raising=False)


@pytest.fixture
def store():
    s = MemoryStore()
    set_store(s)
    yield s
    set_store(None)


@pytest.fixture
def seed_store():
    s = SeedStore()
    set_store(s)
    yield s
    set_store(None)


@pytest.fixture
def client(store):
    return TestClient(app)


@pytest.fixture
def admin(store):
    """A client signed in as the shop owner."""
    app.dependency_overrides[require_admin] = lambda: OWNER
    yield TestClient(app)
    app.dependency_overrides.pop(require_admin, None)


def picture(fmt="PNG", size=(2400, 1200)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, (29, 78, 216)).save(buf, fmt)
    return buf.getvalue()
