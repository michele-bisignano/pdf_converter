# Auto-Updater — Setup e Workflow

## File coinvolti

```
updater.py                     → Logica di aggiornamento
update_router.py               → Endpoint API (/api/update/check, /api/update/apply)
src/frontend/src/components/UpdateBanner.jsx → Banner UI lato frontend
```

---

## 1. Dipendenze

L'updater usa solo la stdlib Python (`urllib`, `hashlib`, `json`). Nessuna dipendenza esterna.

---

## 2. Integrazione main.py

Già integrato: `server.py` include automaticamente `update_router.py` tramite import condizionale:

```python
try:
    from update_router import router as update_router
    app.include_router(update_router)
except ImportError:
    pass
```

---

## 3. Integrazione React

Già integrato: `App.jsx` include `<UpdateBanner />` nel layout principale.

---

## 4. Setup Google Drive (una volta sola)

### Crea la struttura su Drive:
```
releases/
└── pdf_converter/
    ├── version.json
    └── pdf_converter.exe
```

### Carica i file e rendili pubblici:
Per ogni file: tasto destro → **Condividi** → **Chiunque abbia il link** → Visualizzatore

### Ottieni l'ID di ogni file:
Il link Drive ha questa forma:
```
https://drive.google.com/file/d/QUESTO_E_L_ID/view
```
Copia l'ID (la stringa tra `/d/` e `/view`).

### Crea version.json:
```json
{
  "version": "2.0.0",
  "windows_url": "https://drive.google.com/uc?export=download&id=ID_EXE_WINDOWS",
  "mac_url": "https://drive.google.com/uc?export=download&id=ID_ZIP_MAC"
}
```
⚠️ **Non aggiungere `&confirm=t`** — per file grandi Drive richiede un token dinamico.
`updater.py` lo gestisce automaticamente.

Carica su Drive e copia il suo ID.

### Configura updater.py:
```python
# In updater.py (root progetto):
CURRENT_VERSION  = "2.0.0"
VERSION_JSON_URL = "https://drive.google.com/uc?export=download&id=ID_DEL_TUO_JSON"
```

---

## 5. Workflow per ogni aggiornamento

```
1. Modifica il codice

2. Aggiorna CURRENT_VERSION in updater.py (root)
   es. "2.0.0" → "2.0.1"

3. Build
   pyinstaller build.spec
   (l'eseguibile sarà in dist/pdf_converter.exe)

4. Genera version.json
   ./scripts/auto-update.sh 2.0.1 dist/pdf_converter.exe

5. Drive: tasto destro su pdf_converter.exe
   → "Gestisci versioni" → "Carica nuova versione"
   → seleziona dist/pdf_converter.exe
   ⚠️  L'ID rimane lo stesso → url nel JSON non cambia mai

6. Se l'ID del file .exe è cambiato:
   Aggiorna version.json con il nuovo ID, poi caricalo su Drive
   (sovrascrive il file, l'ID del version.json rimane lo stesso)
```

Al prossimo avvio il cliente vede il banner → clicca Aggiorna → fatto.

---

## Note

- In modalità dev (script Python, non .exe) l'updater non fa nulla (`sys.frozen == False`)
- Se Drive non risponde, l'app parte normalmente senza errori
- Il file `.bat` temporaneo si auto-cancella dopo l'aggiornamento
- La variabile d'ambiente `PDF_CONVERTER_UPDATE_URL` permette di testare con un URL diverso senza modificare il codice
- Il flag `--check-update` lancia la verifica all'avvio; `--update-manifest-url URL` permette di specificare un URL personalizzato
