"""
FastAPI server for pdf_converter.
Exposes REST endpoints for PDF-to-Excel conversion.
"""

import os
import uuid
import shutil
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import logging

from src.backend.pdf_to_exel_converter import pdf_to_excel_converter_main

logger = logging.getLogger("pdf_converter.api")

app = FastAPI(title="pdf_converter", version="1.0.0")

# CORS per sviluppo frontend (React su altra porta)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Cartelle ──────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = BASE_DIR / "output"
FRONTEND_DIR = BASE_DIR / "src" / "frontend" / "dist"
TEMP_DIR = BASE_DIR / "temp"

OUTPUT_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)


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


# ── Endpoint API ──────────────────────────────────────────────────────────────


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/api/convert")
async def convert_pdf(
    file: UploadFile = File(...),
    output_path: str = Form(None),
):
    """
    Carica un PDF, lo converte in Excel, restituisce il percorso del file generato.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Il file deve essere un PDF.")

    # Salva il PDF caricato in temp
    temp_id = uuid.uuid4().hex
    pdf_path = TEMP_DIR / f"{temp_id}.pdf"
    try:
        with open(pdf_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore salvataggio file: {e}")

    # Determina percorso output
    if output_path:
        out = Path(output_path)
    else:
        base_name = Path(file.filename).stem
        out = OUTPUT_DIR / f"{base_name}_{temp_id[:8]}.xlsx"

    out.parent.mkdir(parents=True, exist_ok=True)

    try:
        pdf_to_excel_converter_main(str(pdf_path), str(out))
    except Exception as e:
        if pdf_path.exists():
            pdf_path.unlink()
        raise HTTPException(
            status_code=500, detail=f"Errore conversione: {e}"
        )
    finally:
        if pdf_path.exists():
            pdf_path.unlink()

    return {
        "success": True,
        "file_path": str(out),
        "file_name": out.name,
    }


@app.get("/api/download/{filename:path}")
async def download_file(filename: str):
    """Scarica un file Excel generato."""
    file_path = OUTPUT_DIR / filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File non trovato.")
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


# ── Inizializzazione ──────────────────────────────────────────────────────────
_serve_frontend()
