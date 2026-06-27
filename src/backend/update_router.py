"""
FastAPI router for the auto-updater.

Adds 2 endpoints under /api:
  GET  /api/update/check  → controlla se c'e' un update
  POST /api/update/apply  → scarica e applica l'update (riavvia l'app)

This router is automatically included by server.py.
"""

import threading
from fastapi import APIRouter
from src.backend.updater import check_for_update, check_and_apply

router = APIRouter(prefix="/api", tags=["updater"])

_cached_version: str = ""


@router.get("/update/check")
def update_check():
    """
    Check for a newer version.
    Response: { available: bool, version: str }
    """
    global _cached_version
    update = check_for_update()

    if update is not None:
        _cached_version = update.version
        return {"available": True, "version": update.version}

    _cached_version = ""
    return {"available": False, "version": ""}


@router.post("/update/apply")
def update_apply():
    """
    Start the download and application of the update in the background.
    The app will close and reopen automatically.
    Response: { status: "updating" }
    """
    threading.Thread(
        target=check_and_apply,
        daemon=True,
    ).start()
    return {"status": "updating"}
