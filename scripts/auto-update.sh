#!/usr/bin/env bash
# ============================================================================
# auto-update.sh - Genera manifest.json per auto-update di pdf_converter
#
# Utilizzo:
#   ./scripts/auto-update.sh <versione> <percorso_exe>
#
# Esempio:
#   ./scripts/auto-update.sh v1.1.0 dist/pdf_converter.exe
#
# Cosa fa:
#   1. Calcola SHA256 del .exe fornito
#   2. Genera manifest.json con versione, checksum e URL di download
#   3. Il file generato va caricato come asset sulla GitHub Release
#
# Output: manifest.json (nella directory corrente)
# ============================================================================

set -euo pipefail

# ── Funzioni ───────────────────────────────────────────────────────────────────

usage() {
    cat <<EOF
Uso: $0 <versione> <percorso_exe>

Argomenti:
  versione      Tag della release (es. v1.1.0)
  percorso_exe  Path del file .exe da pubblicare

Esempio:
  $0 v1.1.0 dist/pdf_converter.exe

Variabili d'ambiente:
  GITHUB_REPO   Repository GitHub (default: BisyB/pdf_converter)
                Usato per generare l'URL di download nel manifest.
EOF
    exit 1
}

# ── Parse argomenti ───────────────────────────────────────────────────────────

if [[ $# -ne 2 ]]; then
    usage
fi

VERSION="$1"
EXE_PATH="$2"
GITHUB_REPO="${GITHUB_REPO:-BisyB/pdf_converter}"

# Validazioni
if [[ ! -f "$EXE_PATH" ]]; then
    echo "ERRORE: File non trovato: $EXE_PATH" >&2
    exit 1
fi

VERSION_NUM="${VERSION#v}"  # rimuovi eventuale prefisso 'v'

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

# ── Generazione manifest.json ─────────────────────────────────────────────────

cat > manifest.json <<EOF
{
  "version": "${VERSION_NUM}",
  "release_date": "${RELEASE_DATE}",
  "url": "https://github.com/${GITHUB_REPO}/releases/download/${VERSION}/pdf_converter.exe",
  "checksum": "${CHECKSUM}",
  "checksum_type": "sha256",
  "release_notes": "",
  "mandatory": false
}
EOF

# ── Output ─────────────────────────────────────────────────────────────────────

cat <<EOF

============================================
  manifest.json generato con successo
============================================

  Versione:      ${VERSION_NUM}
  Checksum:      ${CHECKSUM:0:16}...
  Release date:  ${RELEASE_DATE}
  URL:           https://github.com/${GITHUB_REPO}/releases/download/${VERSION}/pdf_converter.exe

File creato: manifest.json

Prossimi passi:
  1. Crea una GitHub Release con tag ${VERSION}
  2. Carica pdf_converter.exe come asset
  3. Carica manifest.json come asset
  4. L'app trovera' l'aggiornamento automaticamente

EOF
