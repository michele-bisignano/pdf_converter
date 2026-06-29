# pdf_converter — Frontend

Frontend React per pdf_converter. Si connette al backend FastAPI tramite `/api/`.

## Scripts

```bash
npm install          # Installa dipendenze
npm run dev          # Dev server (porta 5173, proxy /api → localhost:8765)
npm run build        # Build produzione in dist/
npm run preview      # Server locale per testare la build
```

## Build per produzione

```bash
npm run build
```

Il contenuto di `dist/` viene servito staticamente dal backend FastAPI quando si lancia `python main.py` dalla root del progetto.

## Struttura

```
src/
├── App.jsx             → Root component (layout, heartbeat, shutdown)
├── main.jsx            → Entry point
├── components/
│   ├── PDFConverterBox.jsx  → Upload PDF e download Excel
│   └── UpdateBanner.jsx     → Banner aggiornamenti
└── services/
    └── api.js               → Chiamate API (convert, download, heartbeat)
```
