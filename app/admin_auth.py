"""Who may open /admin (AC-5.1): a person signed in to this app through Studio Accounts with the
`owner` or `admin` role. Unlike the public pages, the admin is never open, even while the app's
sign-in switch in the hub is off. Vercel previews are already private behind Vercel's own sign-in,
and the hub only sends people back to the live address, so previews open the admin directly.
"""

from __future__ import annotations

import hashlib
import os
import secrets
from urllib.parse import quote, urlencode

from fastapi import HTTPException, Request
from fastapi.responses import RedirectResponse

from app import studio_auth

ADMIN_ROLES = {"owner", "admin"}
PREVIEW_USER = {"sub": "preview", "name": "Preview visitor", "email": "", "role": "admin"}


def _signin_redirect(request: Request) -> RedirectResponse:
    state, verifier = secrets.token_urlsafe(16), secrets.token_urlsafe(32)
    back = request.url.path + (("?" + request.url.query) if request.url.query else "")
    origin = f"{request.url.scheme}://{request.url.netloc}"
    params = {
        "app": studio_auth.APP,
        "redirect_uri": origin + "/auth/callback",
        "state": state,
        "code_challenge": studio_auth._b64url(hashlib.sha256(verifier.encode()).digest()),
        "code_challenge_method": "S256",
    }
    resp = RedirectResponse(f"{studio_auth.HUB}/auth/login?{urlencode(params)}", status_code=302)
    resp.set_cookie(
        studio_auth.FLOW,
        f"{state}.{verifier}.{quote(back, safe='')}",
        max_age=600,
        path="/auth",
        httponly=True,
        samesite="lax",
        secure=studio_auth._secure(request),
    )
    return resp


def require_admin(request: Request) -> dict:
    """FastAPI dependency for every admin route."""
    if os.environ.get("VERCEL_ENV") == "preview" or os.environ.get("SR_ADMIN_OPEN") == "1":
        return PREVIEW_USER
    user = studio_auth.optional_user(request)
    if not user:
        raise studio_auth._Redirect(_signin_redirect(request))
    if user.get("role") not in ADMIN_ROLES:
        raise HTTPException(
            403,
            detail={
                "code": "not_shop_admin",
                "message": "Your account can't open the shop admin. Ask the founder to give you the owner role.",
            },
        )
    return user
