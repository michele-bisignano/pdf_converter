"""
FastAPI server for pdf_converter.
Exposes REST endpoints for PDF-to-Excel conversion.
"""

import asyncio
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


# -- Lifespan -----------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    TEMP_DIR.mkdir(exist_ok=True)
    _serve_frontend()
    yield
    # Shutdown -- nothing to clean up yet


def _serve_frontend() -> None:
    """Monta i file statici del frontend React, se presenti."""
    if FRONTEND_DIR.is_dir():
        app.mount(
            "/",
            StaticFiles(directory=str(FRONTEND_DIR), html=True),
            name="frontend",
        )
        logger.info("Frontend statico montato da %s", FRONTEND_DIR)
    else:
        logger.warning(
            "Frontend dist non trovato in %s. "
            "Solo API disponibili. Builda il frontend con 'npm run build'.",
            FRONTEND_DIR,
        )

        @app.get("/", response_class=HTMLResponse)
        async def root_warning():
            return HTMLResponse("""
            <html><body style="background:#020203;color:#e4e4e7;font-family:Geist Sans,sans-serif;
            display:flex;justify-content:center;align-items:center;height:100vh;margin:0">
            <div style="text-align:center">
            <h1>pdf_converter</h1>
            <p>Frontend non buildato.</p>
            <p style="color:#a1a1aa">Vai in <code>frontend/</code> ed esegui <code>npm run build</code>.</p>
            <hr style="border-color:#27272a;width:200px">
            <p style="font-size:0.875rem">API disponibili su <a href="/docs" style="color:#3b82f6">/docs</a></p>
            </div></body></html>
            """)


# -- App ----------------------------------------------------------------------

app = FastAPI(
    title="pdf_converter",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS per sviluppo frontend (React su altra porta).
# Nota: Niente allow_credentials=True con allow_origins=["*"]: i browser
# lo bloccano per specifica Fetch. Se servono credenziali, elencare le origini.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include update router (se presente)
try:
    from src.backend.update_router import router as update_router

    app.include_router(update_router)
    logger.info("Update router montato")
except ImportError:
    logger.info("Update router non disponibile")


# -- Endpoint API -------------------------------------------------------------

@app.get("/api/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return HealthResponse(status="ok")


@app.post("/api/convert", response_model=ConvertResponse)
async def convert_pdf(
    file: UploadFile = File(...),
    output_path: str = Form(None),
):
    """
    Carica un PDF, lo converte in Excel, restituisce il percorso del file generato.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Il file deve essere un PDF.")

    temp_id = uuid.uuid4().hex
    pdf_path = TEMP_DIR / f"{temp_id}.pdf"
    try:
        content = await file.read()
        pdf_path.write_bytes(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore salvataggio file: {e}")

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
        raise HTTPException(
            status_code=500, detail=f"Errore conversione: {e}"
        )
    finally:
        if pdf_path.exists():
            pdf_path.unlink()

    return ConvertResponse(
        success=True,
        file_path=str(out),
        file_name=out.name,
        warning=conv_result.get("warning", False),
        warning_message=conv_result.get("warning_message", ""),
        validation=conv_result.get("validation"),
        row_count=conv_result.get("row_count", 0),
    )


@app.get("/api/download/{filename:path}")
async def download_file(filename: str):
    """Scarica un file Excel generato."""
    resolved = (OUTPUT_DIR / filename).resolve()
    if not str(resolved).startswith(str(OUTPUT_DIR.resolve())):
        raise HTTPException(status_code=400, detail="Percorso non consentito.")

    if not resolved.exists() or not resolved.is_file():
        raise HTTPException(status_code=404, detail="File non trovato.")

    return FileResponse(
        path=str(resolved),
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
