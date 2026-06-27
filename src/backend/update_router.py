"""
Router FastAPI per l'auto-updater.

Aggiunge 2 endpoint a /api:
  GET  /api/update/check  → controlla se c'e' un update
  POST /api/update/apply  → scarica e applica l'update (riavvia l'app)

Questo router viene incluso automaticamente da server.py.
"""

import threading
from fastapi import APIRouter
from src.backend.updater import check_for_update, check_and_apply

router = APIRouter(prefix="/api", tags=["updater"])

_cached_version: str = ""


@router.get("/update/check")
def update_check():
    """
    Controlla Drive per una versione piu recente.
    Risposta: { available: bool, version: str }
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
    Avvia il download e l'applicazione dell'update in background.
    L'app si chiudera' e si riaprira' automaticamente.
    Risposta: { status: "updating" }
    """
    threading.Thread(
        target=check_and_apply,
        daemon=True,
    ).start()
    return {"status": "updating"}
