# Changelog

## v2.0.0 (2026-06-29)

Prima release pubblica con frontend React, server FastAPI e auto-updater.

### Nuove funzionalità

- **Frontend React** con interfaccia moderna (Vite + Tailwind + motion/react)
- **Server FastAPI** con API REST, health check, heartbeat watchdog
- **Doppia modalità** — web (default) e CLI (`--cli`)
- **Auto-updater** via Google Drive (controllo all'avvio + aggiornamento one-click)
- **OCR fallback** con Mistral AI per PDF con testo non estraibile
- **Build PyInstaller** — `pyinstaller build.spec` produce `dist/pdf_converter.exe`
- **Salva con nome** — export Excel con dialog di salvataggio (File System Access API)
- **Esportazione anche in caso di errore** di conversione

### Fix

- Corretto ordinamento colonne (Data, Descrizione, Dare, Avere)
- Preservate righe "Saldo" in entrambi i pipeline
- Rimosse righe "Totali" calcolate dall'Excel finale
- Fallback OCR: import corretto per mistralai SDK v2.5.0
- Build API key hardcoded per .exe senza `.env`
- Watchdog heartbeat per rilevare chiusure inattese
- `ExitProcess` pulito su Windows
- Compatibilità type hints Python <3.10 (`Optional`/`Tuple` anziché `X | Y`)
- Cleanup interval polling in UpdateBanner.jsx allo smontaggio

### Technical

- Refactor backend in moduli domain-oriented (`extraction/`, `processing/`, `export/`, `io/`, `alternative/`)
- Validazione saldi unificata tra pipeline primario e fallback
- Docstring inglesi, tipi espliciti, struttura leggibile

### Upgrade notes

Per utenti esistenti: configurare `version.json` su Google Drive e aggiornare
`DEFAULT_MANIFEST_URL` in `updater.py`. Vedi `docs/UPDATER_SETUP.md`.
