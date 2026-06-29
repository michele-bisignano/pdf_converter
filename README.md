# PDF to Excel Converter

Converte automaticamente tabelle da file PDF in fogli Excel, con doppia modalità: web (consigliata) e CLI.

---

## Modalità d'uso

### Web (consigliata)

Avvia il server FastAPI + frontend React e apre automaticamente il browser:

```bash
python main.py
```

Opzioni:
- `--port NUM` — porta personalizzata (default: 8765)
- `--verbose` / `-v` — log dettagliati
- `--check-update` — verifica aggiornamenti all'avvio

### CLI

```bash
python main.py --cli
```

---

## Setup

### Backend
```bash
pip install -r requirements.txt
```

### Frontend (sviluppo)
```bash
cd src/frontend
npm install
npm run build      # produce src/frontend/dist/
```

Per sviluppo frontend:
```bash
npm run dev        # Vite dev server (porta 5173)
```

---

## Build eseguibile

```bash
pip install pyinstaller
pyinstaller build.spec
```

L'eseguibile sarà in `dist/pdf_converter.exe`.

---

## Colonna ordinata

Per richiesta cliente italiano, l'output Excel segue quest'ordine:

| Colonna | Contenuto |
|---------|-----------|
| A | Data |
| C | Descrizione |
| F | Dare / Entrate / Credito |
| G | Avere / Uscite / Debito |

---

## API

Con il server web avviato, la documentazione interattiva è disponibile su `http://localhost:8765/docs`.

| Endpoint | Metodo | Descrizione |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/convert` | POST | Carica PDF → ricevi Excel |
| `/api/download/{filename}` | GET | Scarica file convertito |
| `/api/heartbeat` | POST | Ping liveness (frontend) |
| `/api/shutdown` | POST | Ferma il server |
| `/api/update/check` | GET | Verifica aggiornamenti |
| `/api/update/apply` | POST | Applica aggiornamento |

---

## Banche testate

Funzionanti: BCC, Banco BPM, Credit Agricole
Non funzionante: Intesa Sanpaolo

---

## Licenza

Apache 2.0. Vedi [LICENSE](LICENSE).
