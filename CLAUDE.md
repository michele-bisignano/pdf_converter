# pdf_converter

## Stack
- **Backend**: Python (FastAPI, pdfplumber, pandas, openpyxl, PyMuPDF, Mistral OCR fallback)
- **Frontend**: React + Vite (motion/react, lucide-react)
- **Build**: PyInstaller

## Commands
- Install backend: `pip install -r requirements.txt`
- Install frontend: `cd src/frontend && npm install`
- Build frontend: `cd src/frontend && npm run build`
- Build exe: `pyinstaller build.spec`
- Run web: `python main.py`
- Run CLI: `python main.py --cli`

## Architecture
- `main.py` — entry point (web o CLI)
- `src/backend/server.py` — FastAPI server, watchdog heartbeat, CORS
- `tools/updater/` — auto-update via Google Drive (updater.py + update_router.py)
- `src/frontend/src/` — React app

## Rules
- Non modificare file in `.claude/` senza autorizzazione
- Update system uses Google Drive, not GitHub Releases

## Memory
@.claude/wiki/hot.md
