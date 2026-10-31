"""Studio sign-in for FastAPI apps (tier H), the Python twin of studio-auth/middleware.js.

Copy to `app/studio_auth.py`, set APP below, then in app/main.py:

    from app import studio_auth
    from app.studio_auth import require_user, optional_user
    studio_auth.install(app)        # adds /auth/callback, /auth/me, /auth/logout

    @app.get("/")                       # protected page
    def home(request: Request, user: dict = Depends(require_user)): ...

`require_user` lets everyone in while sign-in is off for this app in the Idea Studio admin,
and sends people to the shared sign-in page while it is on. Needs httpx and pyjwt[crypto].
"""

from __future__ import annotations

import base64
import hashlib
import os
import secrets
import time
from urllib.parse import quote, unquote, urlencode

import httpx
import jwt
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

HUB = os.environ.get("STUDIO_HUB", "https://idea-studio-akkiverse.vercel.app")
APP = "sr-electricals"
PROTECT_IF_UNSURE = True  # True for apps holding private data
SESSION, FLOW = "studio_session", "studio_flow"

router = APIRouter()
_jwks = jwt.PyJWKClient(HUB + "/api/auth/jwks.json", cache_keys=True, lifespan=600)
_setting: dict = {"at": 0.0, "required": None}


def _b64url(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def signin_required() -> bool:
    if _setting["required"] is not None and time.time() - _setting["at"] < 60:
        return _setting["required"]
    try:
        r = httpx.get(f"{HUB}/api/auth/apps/{APP}", timeout=2.5)
        if r.status_code == 200:
            _setting.update(at=time.time(), required=bool(r.json().get("signin_required")))
            return _setting["required"]
        if r.status_code == 404:
            _setting.update(at=time.time(), required=False)
            return False
    except httpx.HTTPError:
        pass
    return PROTECT_IF_UNSURE if _setting["required"] is None else _setting["required"]


def _verify(token: str) -> dict | None:
    try:
        key = _jwks.get_signing_key_from_jwt(token).key
        return jwt.decode(token, key, algorithms=["EdDSA"], audience=APP, issuer=HUB)
    except (jwt.PyJWTError, httpx.HTTPError, ValueError):
        return None


def optional_user(request: Request) -> dict | None:
    token = request.cookies.get(SESSION)
    return _verify(token) if token else None


def _secure(request: Request) -> bool:
    return request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https"


def require_user(request: Request) -> dict:
    """FastAPI dependency: the signed-in user (an empty dict while sign-in is off)."""
    if os.environ.get("VERCEL_ENV") == "preview" or not signin_required():
        return optional_user(request) or {}
    u = optional_user(request)
    if u:
        return u
    if request.url.path.startswith("/api/"):
        raise HTTPException(401, detail={"code": "signin_required", "message": "Sign in to use this app."})
    state, verifier = secrets.token_urlsafe(16), secrets.token_urlsafe(32)
    back = request.url.path + (("?" + request.url.query) if request.url.query else "")
    origin = f"{request.url.scheme}://{request.url.netloc}"
    params = {
        "app": APP, "redirect_uri": origin + "/auth/callback", "state": state,
        "code_challenge": _b64url(hashlib.sha256(verifier.encode()).digest()), "code_challenge_method": "S256",
    }
    resp = RedirectResponse(f"{HUB}/auth/login?{urlencode(params)}", status_code=302)
    resp.set_cookie(FLOW, f"{state}.{verifier}.{quote(back, safe='')}", max_age=600, path="/auth", httponly=True, samesite="lax", secure=_secure(request))
    raise _Redirect(resp)


class _Redirect(Exception):
    def __init__(self, response):
        self.response = response


def install(app) -> None:
    """Call once: app.include_router(router) plus the handler that turns sign-in redirects into responses."""
    app.include_router(router)

    @app.exception_handler(_Redirect)
    async def _redirect_handler(_request, exc: _Redirect):
        return exc.response


def _problem(text: str, status: int) -> HTMLResponse:
    return HTMLResponse(
        f'<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Sign-in didn\'t finish</title>'
        f'<body style="font:16px/1.5 system-ui,sans-serif;max-width:32rem;margin:15vh auto;padding:0 16px"><h1 style="font-size:1.4rem">Sign-in didn\'t finish</h1><p>{text}</p><p><a href="/">Try again</a></p></body>',
        status_code=status, headers={"Cache-Control": "no-store"},
    )


@router.get("/auth/callback", include_in_schema=False)
def callback(request: Request, code: str = "", state: str = ""):
    parts = (request.cookies.get(FLOW) or "").split(".", 2)
    if len(parts) != 3 or not code or state != parts[0]:
        return _problem("The sign-in link expired or was opened in another browser. Please sign in again.", 400)
    verifier, back = parts[1], unquote(parts[2]) or "/"
    origin = f"{request.url.scheme}://{request.url.netloc}"
    try:
        r = httpx.post(f"{HUB}/api/auth/token", json={"app": APP, "code": code, "redirect_uri": origin + "/auth/callback", "code_verifier": verifier}, timeout=8)
        r.raise_for_status()
        token = r.json()["access_token"]
    except (httpx.HTTPError, KeyError, ValueError):
        return _problem("We couldn't confirm your sign-in. Please try again in a moment.", 502)
    claims = _verify(token)
    if not claims:
        return _problem("We couldn't confirm your sign-in. Please try again in a moment.", 502)
    resp = RedirectResponse(back if back.startswith("/") and not back.startswith("//") else "/", status_code=302)
    resp.set_cookie(SESSION, token, max_age=max(60, int(claims["exp"] - time.time())), path="/", httponly=True, samesite="lax", secure=_secure(request))
    resp.delete_cookie(FLOW, path="/auth")
    return resp


@router.get("/auth/me", include_in_schema=False)
def me(request: Request):
    u = optional_user(request)
    body = {"signed_in": True, "user": {"id": u["sub"], "name": u["name"], "email": u["email"], "role": u["role"]}} if u else {"signed_in": False}
    return JSONResponse(body, headers={"Cache-Control": "no-store"})


@router.get("/auth/logout", include_in_schema=False)
def logout():
    resp = RedirectResponse("/", status_code=302)
    resp.delete_cookie(SESSION, path="/")
    return resp
