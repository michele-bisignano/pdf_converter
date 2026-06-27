# Auto-Updater — Setup e Workflow

## File da integrare nel progetto

```
updater.py        → root del progetto
update_router.py  → root del progetto
UpdateBanner.jsx  → src/components/ (o dove tieni i componenti)
```

---

## 1. Dipendenze

Aggiungi a `requirements.txt` se non c'è:
```
requests
```

---

## 2. Integrazione main.py

Aggiungi queste 2 righe dopo aver creato l'istanza `app = FastAPI(...)`:

```python
from update_router import router as update_router
app.include_router(update_router)
```

---

## 3. Integrazione React

In `App.jsx` (o nel tuo layout principale):

```jsx
import UpdateBanner from "./components/UpdateBanner";

export default function App() {
  return (
    <>
      <UpdateBanner />
      {/* ... resto dell'app */}
    </>
  );
}
```

---

## 4. Setup Google Drive (una volta sola)

### Crea la struttura su Drive:
```
releases/
└── nome-app/
    ├── version.json
    ├── nome-app-windows.exe
    └── nome-app-mac.zip          ← futuro
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
  "windows_url": "https://drive.google.com/uc?export=download&id=ID_EXE_WINDOWS&confirm=t",
  "mac_url": "https://drive.google.com/uc?export=download&id=ID_ZIP_MAC&confirm=t"
}
```
Carica su Drive e copia il suo ID.

### Configura updater.py:
```python
CURRENT_VERSION  = "2.0.0"
VERSION_JSON_URL = "https://drive.google.com/uc?export=download&id=ID_DEL_JSON"
```

---

## 5. Workflow per ogni aggiornamento

```
1. Modifica il codice

2. Aggiorna CURRENT_VERSION in updater.py
   es. "1.0.0" → "1.0.1"

3. Build
   pyinstaller --onefile --name nome-app-windows main.py

4. Drive: tasto destro su nome-app-windows.exe
   → "Gestisci versioni" → "Carica nuova versione"
   → seleziona dist/nome-app-windows.exe
   ⚠️  L'ID rimane lo stesso → windows_url nel JSON non cambia mai

5. Drive: apri version.json → modifica "version": "1.0.1" → salva
   (sovrascrive il file, l'ID rimane lo stesso)
```

Al prossimo avvio il cliente vede il banner → clicca Aggiorna → fatto.

---

## Note

- In modalità dev (script Python) l'updater non fa nulla (`is_packaged() == False`)
- Se Drive non risponde, l'app parte normalmente senza errori
- Il file `.bat` / `.sh` temporaneo si auto-cancella dopo l'aggiornamento
- Per macOS: `zip -r nome-app-mac.zip NomeApp.app` prima di caricare su Drive
