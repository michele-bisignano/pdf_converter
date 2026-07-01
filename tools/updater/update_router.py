"""
Router FastAPI per l'auto-updater.

Aggiunge 3 endpoint a /api:
  GET  /api/update/check  → controlla se c'è un update
  POST /api/update/apply  → scarica e applica l'update (riavvia l'app)
  GET  /api/health        → usato dal frontend per sapere quando il server è tornato su

INTEGRAZIONE in main.py (aggiungi queste 2 righe):

  from tools.updater.update_router import router as update_router
  app.include_router(update_router)
"""

import threading
from fastapi import APIRouter
from tools.updater.updater import check_for_update, do_update

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


@router.post("/update/apply")
def update_apply():
    """
    Avvia il download e l'applicazione dell'update in background.
    L'app si chiuderà e si riaprirà automaticamente.
    Risposta: { status: "updating" } oppure { status: "no_update_cached" }

    Nota: richiede che /update/check sia stato chiamato prima (il frontend
    lo fa sempre al mount). Se _cached_release è vuoto, ri-controlla al volo
    invece di fallire silenziosamente.
    """
    global _cached_release

    release = _cached_release
    if not release:
        _, _, release = check_for_update()
        if not release:
            return {"status": "no_update_available"}

    threading.Thread(
        target=lambda: do_update(release),
        daemon=True,
    ).start()
    return {"status": "updating"}


@router.get("/health")
def health():
    """Endpoint di health check — usato dal frontend per rilevare il riavvio."""
    return {"ok": True}
