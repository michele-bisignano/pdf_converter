#!/usr/bin/env bash
# ============================================================================
# auto-update.sh - Genera version.json per auto-update di pdf_converter
#
# Utilizzo:
#   ./scripts/auto-update.sh <versione> <percorso_exe>
#
# Esempio:
#   ./scripts/auto-update.sh 2.0.1 dist/pdf_converter.exe
#
# Cosa fa:
#   1. Calcola SHA256 del .exe fornito
#   2. Genera version.json con versione, checksum e URL Drive
#   3. Il file generato va caricato su Google Drive
#
# Output: version.json (nella directory corrente)
#
# Workflow Drive:
#   1. ./scripts/auto-update.sh 2.0.1 dist/pdf_converter.exe
#   2. Carica pdf_converter.exe su Drive (Gestisci versioni → Carica nuova versione)
#   3. Copia l'ID del file .exe e aggiorna version.json con l'ID corretto
#   4. Aggiorna version.json su Drive (sovrascrivi, l'ID non cambia)
# ============================================================================

set -euo pipefail

# ── Funzioni ───────────────────────────────────────────────────────────────────

usage() {
    cat <<EOF
Uso: $0 <versione> <percorso_exe>

Argomenti:
  versione      Versione (es. 2.0.1)
  percorso_exe  Path del file .exe da pubblicare

Esempio:
  $0 2.0.1 dist/pdf_converter.exe

Variabili d'ambiente (opzionali):
  DRIVE_EXE_ID  ID del file .exe su Google Drive (default: FILE_ID_EXE)
EOF
    exit 1
}

# ── Parse argomenti ───────────────────────────────────────────────────────────

if [[ $# -ne 2 ]]; then
    usage
fi

VERSION="$1"
EXE_PATH="$2"
DRIVE_EXE_ID="${DRIVE_EXE_ID:-FILE_ID_EXE}"

# Validazioni
if [[ ! -f "$EXE_PATH" ]]; then
    echo "ERRORE: File non trovato: $EXE_PATH" >&2
    exit 1
fi

# ── Calcolo checksum ──────────────────────────────────────────────────────────

echo "Calcolo SHA256 di $EXE_PATH ..."

if command -v sha256sum &>/dev/null; then
    CHECKSUM=$(sha256sum "$EXE_PATH" | cut -d' ' -f1)
elif command -v shasum &>/dev/null; then
    CHECKSUM=$(shasum -a 256 "$EXE_PATH" | cut -d' ' -f1)
elif command -v openssl &>/dev/null; then
    CHECKSUM=$(openssl dgst -sha256 "$EXE_PATH" | cut -d' ' -f2)
else
    echo "ERRORE: Nessun tool per SHA256 trovato (sha256sum, shasum, openssl)." >&2
    exit 1
fi

RELEASE_DATE=$(date -u +%Y-%m-%d)

# ── Generazione version.json ──────────────────────────────────────────────────

cat > version.json <<EOF
{
  "version": "${VERSION}",
  "release_date": "${RELEASE_DATE}",
  "url": "https://drive.google.com/uc?export=download&id=${DRIVE_EXE_ID}&confirm=t",
  "checksum": "${CHECKSUM}",
  "checksum_type": "sha256",
  "release_notes": "",
  "mandatory": false
}
EOF

# ── Output ─────────────────────────────────────────────────────────────────────

cat <<EOF

============================================
  version.json generato con successo
============================================

  Versione:      ${VERSION}
  Checksum:      ${CHECKSUM:0:16}...
  Release date:  ${RELEASE_DATE}
  URL Drive:     https://drive.google.com/uc?export=download&id=${DRIVE_EXE_ID}&confirm=t

File creato: version.json

Prossimi passi:
  1. Carica pdf_converter.exe su Google Drive (stesso file, ID invariato)
  2. Apri version.json → sostituisci DRIVE_EXE_ID con l'ID reale del file
  3. Carica version.json su Google Drive (sovrascrivi il precedente)
  4. Aggiorna VERSION_JSON_URL in tools/updater/updater.py con l'ID del version.json

EOF
