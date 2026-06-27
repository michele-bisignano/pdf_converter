"""
Router FastAPI per l'auto-updater.

Aggiunge 3 endpoint a /api:
  GET  /api/update/check  → controlla se c'è un update
  POST /api/update/apply  → scarica e applica l'update (riavvia l'app)
  GET  /api/health        → usato dal frontend per sapere quando il server è tornato su

INTEGRAZIONE in main.py (aggiungi queste 2 righe):

  from update_router import router as update_router
  app.include_router(update_router)
"""

import threading
from fastapi import APIRouter
from updater import check_for_update, do_update

router = APIRouter(prefix="/api", tags=["updater"])

# Cache della release corrente (evita doppio fetch al momento dell'apply)
_cached_release: dict = {}


@router.get("/update/check")
def update_check():
    """
    Controlla Drive per una versione più recente.
    Risposta: { available: bool, version: str }
    """
    global _cached_release
    available, latest, release = check_for_update()
    _cached_release = release
    return {"available": available, "version": latest}


@router.post("/api/update/apply")
def update_apply():
    """
    Avvia il download e l'applicazione dell'update in background.
    L'app si chiuderà e si riaprirà automaticamente.
    Risposta: { status: "updating" }
    """
    threading.Thread(
        target=lambda: do_update(_cached_release),
        daemon=True,
    ).start()
    return {"status": "updating"}


@router.get("/health")
def health():
    """Endpoint di health check — usato dal frontend per rilevare il riavvio."""
    return {"ok": True}
