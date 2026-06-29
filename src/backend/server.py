"""
FastAPI server for pdf_converter.
Exposes REST endpoints for PDF-to-Excel conversion.
"""

import asyncio
import os
import platform
import threading
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging

from src.backend.pdf_to_exel_converter import pdf_to_excel_converter_main

logger = logging.getLogger("pdf_converter.api")


# -- Response models ----------------------------------------------------------

class HealthResponse(BaseModel):
    status: str


class ConvertResponse(BaseModel):
    success: bool
    file_path: str
    file_name: str
    warning: bool = False
    warning_message: str = ""
    validation: Any = None
    row_count: int = 0


# -- Paths --------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = BASE_DIR / "output"
FRONTEND_DIR = BASE_DIR / "src" / "frontend" / "dist"
TEMP_DIR = BASE_DIR / "temp"


# -- Watchdog (auto-shutdown on lost heartbeat) -------------------------------
#
# The frontend tab sends a heartbeat every HEARTBEAT_INTERVAL_S seconds while
# it's open. If the browser is closed (or crashes) the heartbeat stops, and
# this background thread kills the process after HEARTBEAT_TIMEOUT_S of
# silence. This acts as a safety net for cases where the explicit
# /api/shutdown call from the "Exit" button never arrives (e.g. the tab is
# closed before the request is sent, or the request is cancelled mid-flight).
HEARTBEAT_INTERVAL_S = 5
HEARTBEAT_TIMEOUT_S = 20  # must be a few heartbeats wide to tolerate hiccups

_last_heartbeat: float | None = None
_watchdog_lock = threading.Lock()


def _kill_process() -> None:
    """Terminate the current process unconditionally.

    On Windows, signal-based approaches (CTRL_BREAK_EVENT) can fail when
    the process runs without a console (e.g. launched from a packaged
    .exe or from Git Bash), so we go through the native kernel32 call
    instead. On POSIX, os._exit bypasses cleanup handlers and guarantees
    termination.
    """
    if platform.system() == "Windows":
        import ctypes
        ctypes.windll.kernel32.ExitProcess(0)
    else:
        os._exit(0)


def _watchdog_loop() -> None:
    """Background thread: auto-shutdown if heartbeats stop arriving.

    Only starts counting once the first heartbeat is received, so a
    frontend that's never opened (e.g. pure API usage) won't trigger
    an unwanted shutdown.
    """
    while True:
        time.sleep(HEARTBEAT_INTERVAL_S)
        with _watchdog_lock:
            last = _last_heartbeat
        if last is None:
            continue  # no client has connected yet
        if time.time() - last > HEARTBEAT_TIMEOUT_S:
            logger.warning(
                "No heartbeat received for %.0fs; shutting down.",
                time.time() - last,
            )
            _kill_process()
            return


# -- Lifespan -----------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    TEMP_DIR.mkdir(exist_ok=True)
    _serve_frontend()
    threading.Thread(target=_watchdog_loop, daemon=True).start()
    yield
    # Shutdown -- nothing to clean up yet


def _serve_frontend() -> None:
    """Mount React frontend static files if present."""
    if FRONTEND_DIR.is_dir():
        app.mount(
            "/",
            StaticFiles(directory=str(FRONTEND_DIR), html=True),
            name="frontend",
        )
        logger.info("Frontend static files mounted from %s", FRONTEND_DIR)
    else:
        logger.warning(
            "Frontend dist not found at %s. "
            "Only API endpoints available. Build the frontend with 'npm run build'.",
            FRONTEND_DIR,
        )

        @app.get("/", response_class=HTMLResponse)
        async def root_warning():
            return HTMLResponse("""
            <html><body style="background:#020203;color:#e4e4e7;font-family:Geist Sans,sans-serif;
            display:flex;justify-content:center;align-items:center;height:100vh;margin:0">
            <div style="text-align:center">
            <h1>pdf_converter</h1>
            <p>Frontend not built.</p>
            <p style="color:#a1a1aa">Go to <code>frontend/</code> and run <code>npm run build</code>.</p>
            <hr style="border-color:#27272a;width:200px">
            <p style="font-size:0.875rem">API available at <a href="/docs" style="color:#3b82f6">/docs</a></p>
            </div></body></html>
            """)


# -- App ----------------------------------------------------------------------

app = FastAPI(
    title="pdf_converter",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS for frontend development (React on a different port).
# Note: No allow_credentials=True with allow_origins=["*"]: browsers
# block it per the Fetch specification. If credentials are needed, list the origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include update router (if present)
try:
    from src.backend.update_router import router as update_router

    app.include_router(update_router)
    logger.info("Update router mounted")
except ImportError:
    logger.info("Update router not available")


# -- Endpoint API -------------------------------------------------------------

@app.get("/api/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return HealthResponse(status="ok")


@app.post("/api/heartbeat")
async def heartbeat():
    """Record a liveness ping from an open frontend tab.

    Called periodically by the frontend while the tab is open. If these
    stop arriving (tab closed, browser crashed, network cut), the
    watchdog thread shuts the server down automatically -- see
    HEARTBEAT_TIMEOUT_S.
    """
    global _last_heartbeat
    with _watchdog_lock:
        _last_heartbeat = time.time()
    return {"status": "ok"}


@app.post("/api/shutdown")
async def shutdown():
    """Shut down the server process.

    Uses a threading.Timer to delay the kill so the HTTP response can
    be sent first. This is the explicit/fast path triggered by the
    "Exit" button; the heartbeat watchdog (see above) is the fallback
    for when this request never arrives (e.g. tab closed before the
    request could be sent or completed).
    """
    logger.info("Shutdown requested via API")
    threading.Timer(0.5, _kill_process).start()
    return {"status": "shutting_down"}


@app.post("/api/convert", response_model=ConvertResponse)
async def convert_pdf(
    file: UploadFile = File(...),
    output_path: str = Form(None),
):
    """
    Upload a PDF, convert it to Excel, return the path of the generated file.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF.")

    temp_id = uuid.uuid4().hex
    pdf_path = TEMP_DIR / f"{temp_id}.pdf"
    try:
        content = await file.read()
        pdf_path.write_bytes(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {e}")

    if output_path:
        out = Path(output_path)
    else:
        base_name = Path(file.filename).stem
        out = OUTPUT_DIR / f"{base_name}_{temp_id[:8]}.xlsx"

    out.parent.mkdir(parents=True, exist_ok=True)

    try:
        conv_result = await asyncio.to_thread(
            pdf_to_excel_converter_main, str(pdf_path), str(out)
        )
    except Exception as e:
        logger.exception("Conversion failed (file may still exist on disk)")
        conv_result = {"success": False, "warning": True, "warning_message": f"Conversion error: {e}"}
    finally:
        if pdf_path.exists():
            pdf_path.unlink()

    file_exists = out.exists() and out.is_file()
    return ConvertResponse(
        success=conv_result.get("success", False),
        file_path=str(out) if file_exists else "",
        file_name=out.name if file_exists else "",
        warning=conv_result.get("warning", False),
        warning_message=conv_result.get("warning_message", ""),
        validation=conv_result.get("validation"),
        row_count=conv_result.get("row_count", 0),
    )


@app.get("/api/download/{filename:path}")
async def download_file(filename: str):
    """Download a generated Excel file."""
    resolved = (OUTPUT_DIR / filename).resolve()
    if not str(resolved).startswith(str(OUTPUT_DIR.resolve())):
        raise HTTPException(status_code=400, detail="Path not allowed.")

    if not resolved.exists() or not resolved.is_file():
        raise HTTPException(status_code=404, detail="File not found.")

    return FileResponse(
        path=str(resolved),
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
