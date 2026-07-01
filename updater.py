"""
Auto-updater per app PyInstaller — Windows + macOS.

CONFIGURA:
  CURRENT_VERSION  → aggiorna prima di ogni build
  VERSION_JSON_URL → URL diretto al version.json su Drive

Non toccare il resto.
"""

import sys
import subprocess
import platform
import threading
from pathlib import Path
from typing import Optional, Tuple

import requests  # pip install requests

# ── CONFIGURA ──────────────────────────────────────────────────────────────────
CURRENT_VERSION  = "1.0.0"
VERSION_JSON_URL = "https://drive.google.com/uc?export=download&id=ID_DEL_TUO_JSON"
# ───────────────────────────────────────────────────────────────────────────────


def is_packaged() -> bool:
    return getattr(sys, "frozen", False)


def _compare(v1: str, v2: str) -> int:
    def parse(v):
        return [int(x) for x in v.lstrip("v").split(".")]
    a, b = parse(v1), parse(v2)
    return (a > b) - (a < b)


def _get_release() -> Optional[dict]:
    try:
        r = requests.get(VERSION_JSON_URL, timeout=5)
        r.raise_for_status()
        data = r.json()
        return {
            "tag_name": data["version"],
            "assets": [
                {"platform": "Windows", "url": data.get("windows_url", "")},
                {"platform": "Darwin",  "url": data.get("mac_url", "")},
            ],
        }
    except Exception:
        return None


def _asset_url(release: dict) -> Optional[str]:
    system = platform.system()
    for a in release.get("assets", []):
        if a["platform"] == system and a["url"]:
            return a["url"]
    return None


def _extract_confirm_token(html: str) -> Optional[str]:
    """
    Estrae il confirm token dinamico dalla pagina di avviso "Google Drive
    non può controllare i virus" che Google mostra per file > ~100MB.
    Il token cambia ad ogni richiesta e scade dopo 10-15 minuti.
    """
    import re
    match = re.search(r'confirm=([0-9A-Za-z_-]+)', html)
    return match.group(1) if match else None


def _download(url: str, dest: Path, on_progress=None) -> bool:
    """
    Scarica un file da Drive gestendo sia file piccoli (download diretto)
    sia file grandi (pagina di avviso virus scan con token dinamico).
    """
    try:
        session = requests.Session()

        with session.get(url, stream=True, timeout=120) as r:
            r.raise_for_status()
            content_type = r.headers.get("content-type", "")

            # File grande → Drive risponde con HTML invece del binario
            if "text/html" in content_type:
                html = r.text
                token = _extract_confirm_token(html)
                if not token:
                    print("[updater] impossibile estrarre confirm token da Drive")
                    return False

                # Riprova con il token dinamico
                retry_url = url + ("&" if "?" in url else "?") + f"confirm={token}"
                with session.get(retry_url, stream=True, timeout=120) as r2:
                    r2.raise_for_status()
                    return _write_stream(r2, dest, on_progress)

            return _write_stream(r, dest, on_progress)

    except Exception as e:
        print(f"[updater] download error: {e}")
        return False


def _write_stream(response, dest: Path, on_progress=None) -> bool:
    total = int(response.headers.get("content-length", 0))
    done = 0
    with open(dest, "wb") as f:
        for chunk in response.iter_content(8192):
            f.write(chunk)
            done += len(chunk)
            if on_progress and total:
                on_progress(done / total)
    return True


def _apply_windows(current: Path, new_exe: Path) -> None:
    bat = current.parent / "_updater.bat"
    bat.write_text(
        f"@echo off\r\n"
        f"timeout /t 4 /nobreak >nul\r\n"
        f"move /y \"{new_exe}\" \"{current}\"\r\n"
        f"start \"\" \"{current}\"\r\n"
        f"del \"%~f0\"\r\n",
        encoding="utf-8",
    )
    subprocess.Popen(
        ["cmd", "/c", str(bat)],
        creationflags=subprocess.CREATE_NO_WINDOW,
        close_fds=True,
    )
    sys.exit(0)


def _apply_mac(new_zip: Path) -> None:
    # sys.executable è dentro .app/Contents/MacOS/ → risali al bundle
    app_bundle = Path(sys.executable).parent.parent.parent
    sh = app_bundle.parent / "_updater.sh"
    sh.write_text(
        f"#!/bin/bash\n"
        f"sleep 4\n"
        f"rm -rf \"{app_bundle}\"\n"
        f"unzip -o \"{new_zip}\" -d \"{app_bundle.parent}\"\n"
        f"open \"{app_bundle}\"\n"
        f"rm -f \"{new_zip}\"\n"
        f"rm -- \"$0\"\n"
    )
    sh.chmod(0o755)
    subprocess.Popen(["/bin/bash", str(sh)])
    sys.exit(0)


# ── API PUBBLICA ────────────────────────────────────────────────────────────────

def check_for_update() -> Tuple[bool, str, dict]:
    """
    Returns (available, latest_version, release_dict).
    Ritorna (False, CURRENT_VERSION, {}) in dev mode o se Drive non risponde.
    """
    if not is_packaged():
        return False, CURRENT_VERSION, {}

    release = _get_release()
    if not release:
        return False, CURRENT_VERSION, {}

    latest    = release["tag_name"].lstrip("v")
    available = _compare(latest, CURRENT_VERSION) > 0
    return available, latest, release


def do_update(release: dict, on_progress=None) -> None:
    """Scarica e applica l'update. Se riesce, chiama sys.exit()."""
    url = _asset_url(release)
    if not url:
        print("[updater] nessun asset compatibile nella release")
        return

    system = platform.system()
    exe    = Path(sys.executable)

    if system == "Windows":
        dest = exe.parent / "_update_new.exe"
        if _download(url, dest, on_progress):
            _apply_windows(exe, dest)

    elif system == "Darwin":
        # exe.parent è dentro .app/Contents/MacOS/ — lo zip DEVE stare
        # fuori dal bundle, altrimenti "rm -rf .app" lo cancella prima
        # che venga estratto.
        app_bundle = exe.parent.parent.parent
        dest = app_bundle.parent / "_update_new.zip"
        if _download(url, dest, on_progress):
            _apply_mac(dest)


def check_and_update_async(on_update_available=None, on_no_update=None) -> None:
    """Check non bloccante in background thread."""
    def _run():
        available, latest, release = check_for_update()
        if available and on_update_available:
            on_update_available(latest, release)
        elif not available and on_no_update:
            on_no_update()

    threading.Thread(target=_run, daemon=True).start()
