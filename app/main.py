"""SR Electricals: FastAPI app (tier H). Vercel loads `app` from this file."""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException

from app import studio_auth
from app.adapters.store import get_store
from app.routes import admin, api, pages
from app.web import render

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger("sr-electricals")

app = FastAPI(
    title="SR Electricals",
    summary="Shop website for SR Electrical, Deoghar.",
    version="0.1.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    redoc_url=None,
)
studio_auth.install(app)
app.include_router(api.router)
app.include_router(admin.router)
app.include_router(pages.router)

# On Vercel, files in public/ are served by the CDN at the site root. Locally we serve them here.
_PUBLIC = Path(__file__).resolve().parent.parent / "public"
if (_PUBLIC / "static").is_dir():
    app.mount("/static", StaticFiles(directory=_PUBLIC / "static"), name="static")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon() -> RedirectResponse:
    return RedirectResponse("/static/favicon.svg", status_code=307)


@app.get("/healthz", include_in_schema=False)
@app.get("/api/health", include_in_schema=False)
def health() -> dict:
    return {"ok": True, "store": get_store().kind}


def _error(code: str, message: str, status: int) -> JSONResponse:
    return JSONResponse({"error": {"code": code, "message": message}}, status_code=status)


@app.exception_handler(RequestValidationError)
async def _validation(request: Request, exc: RequestValidationError):
    errs = exc.errors()
    msg = str(errs[0].get("msg", "")).removeprefix("Value error, ") if errs else ""
    if errs and errs[0].get("loc", [None])[-1] == "qty":
        msg = "Quantities must be whole numbers from 1 to 9999."
    return _error("invalid_request", msg or "Some of the details sent weren't valid.", 422)


@app.exception_handler(HTTPException)
async def _http(request: Request, exc: HTTPException):
    detail = exc.detail if isinstance(exc.detail, dict) else {}
    if request.url.path.startswith("/api/"):
        if detail.get("code"):
            return _error(detail["code"], detail.get("message", ""), exc.status_code)
        msg = "There is nothing at this address." if exc.status_code == 404 else str(exc.detail)
        return _error("not_found" if exc.status_code == 404 else "error", msg, exc.status_code)
    if exc.status_code == 404:
        title, message = "Page not found", "We couldn't find that page. It may have been removed or renamed."
    elif detail.get("message"):
        title, message = "Not allowed", detail["message"]
    else:
        title, message = "Something went wrong", "That didn't work. Please try again."
    return render(request, "error.html", {"title": title, "message": message}, status_code=exc.status_code)


@app.exception_handler(Exception)
async def _unexpected(request: Request, exc: Exception):  # pragma: no cover - safety net
    log.exception("Unexpected error on %s", request.url.path)
    if request.url.path.startswith("/api/"):
        return _error("server_error", "Something went wrong on our side. Please try again.", 500)
    return render(
        request,
        "error.html",
        {
            "title": "Something went wrong",
            "message": "Couldn't load this page, please try again in a moment, or call us.",
        },
        status_code=500,
    )
