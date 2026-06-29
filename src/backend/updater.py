"""
Auto-update module for pdf_converter (Windows PyInstaller).

Architecture
------------
Versions are distributed via Google Drive. Each release consists of:
  - pdf_converter.exe  (the new binary, uploaded as a new Drive version)
  - version.json       (version metadata + checksum, stored on Drive)

On startup (--check-update) the module:
  1. Fetches version.json from Google Drive
  2. Compares versions
  3. If a newer version exists → downloads the .exe to %TEMP%
  4. Launches update.bat that waits for this process to exit,
     replaces the .exe, and restarts the app

Drive setup
-----------
Upload files to Google Drive, share as "Anyone with the link → Viewer",
and build a version.json with the Drive file IDs:

  {
    "version": "2.0.0",
    "url": "https://drive.google.com/uc?export=download&id=FILE_ID_EXE&confirm=t",
    "checksum": "sha256 hex string",
    "checksum_type": "sha256",
    "release_date": "2026-06-27",
    "release_notes": "Bug fixes and improvements",
    "mandatory": false
  }

Set VERSION_JSON_URL below to the Drive download link of that version.json.
The env var PDF_CONVERTER_UPDATE_URL or the --update-manifest-url CLI flag
can override it at runtime.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

logger = logging.getLogger("pdf_converter.updater")

# ── Build-time override ───────────────────────────────────────────────────────
# Set this to the real manifest URL before running PyInstaller.
# The URL is embedded in the .exe (visible via decompilation — tradeoff accepted).
# In development, the PDF_CONVERTER_UPDATE_URL env var or --update-manifest-url
# flag take precedence.
_BUILD_MANIFEST_URL: str = ""

# ── Defaults ───────────────────────────────────────────────────────────────────

DEFAULT_MANIFEST_URL = (
    "https://drive.google.com/uc?export=download&id=YOUR_VERSION_JSON_ID&confirm=t"
)

ENV_MANIFEST_URL = "PDF_CONVERTER_UPDATE_URL"

UPDATE_DIR = Path(tempfile.gettempdir()) / "pdf_converter_update"

CURRENT_VERSION = "2.0.0"


# ── Data ───────────────────────────────────────────────────────────────────────

@dataclass
class UpdateInfo:
    """Parsed information about an available update."""

    version: str
    url: str
    checksum: str = ""
    checksum_type: str = "sha256"
    release_date: str = ""
    release_notes: str = ""
    mandatory: bool = False


# ── Version helpers ────────────────────────────────────────────────────────────


def _parse_version(ver: str) -> Tuple[int, ...]:
    """Parse '1.2.3' → (1, 2, 3) for comparison.

    Falls back to (0,) on malformed input so we never crash.
    """
    try:
        return tuple(int(x) for x in ver.strip().split("."))
    except (ValueError, AttributeError):
        return (0,)  # type: ignore[return-value]


def _is_newer(remote: str, current: str) -> bool:
    """True if *remote* is a strictly greater version than *current*."""
    return _parse_version(remote) > _parse_version(current)


# ── Manifest fetching ──────────────────────────────────────────────────────────


def _resolve_manifest_url(cli_url: Optional[str] = None) -> str:
    """Resolve the manifest URL: CLI arg > env var > build-time > default."""
    if cli_url:
        return cli_url
    env_url = os.environ.get(ENV_MANIFEST_URL)
    if env_url:
        return env_url
    if _BUILD_MANIFEST_URL:
        return _BUILD_MANIFEST_URL
    return DEFAULT_MANIFEST_URL


def fetch_manifest(manifest_url: str) -> Optional[dict]:
    """Download and parse the remote manifest.json.

    Returns None on any network / parse error.
    """
    logger.info("Fetching update manifest from %s", manifest_url)
    try:
        req = Request(manifest_url, headers={"User-Agent": "pdf_converter-updater/1.0"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        logger.debug("Manifest content: %s", data)
        return data
    except URLError as e:
        logger.warning("Network error fetching manifest: %s", e)
    except json.JSONDecodeError as e:
        logger.warning("Invalid JSON in manifest: %s", e)
    except OSError as e:
        logger.warning("IO error fetching manifest: %s", e)
    return None


# ── Update check ───────────────────────────────────────────────────────────────


def check_for_update(manifest_url: Optional[str] = None) -> Optional[UpdateInfo]:
    """Check whether a newer version exists.

    Returns an ``UpdateInfo`` if one is available, or ``None``.
    """
    url = _resolve_manifest_url(manifest_url)
    manifest = fetch_manifest(url)
    if manifest is None:
        return None

    remote_ver = manifest.get("version", "")
    if not remote_ver:
        logger.warning("Manifest missing 'version' field")
        return None

    if not _is_newer(remote_ver, CURRENT_VERSION):
        logger.info("Already at latest version (%s)", CURRENT_VERSION)
        return None

    return UpdateInfo(
        version=remote_ver,
        url=manifest.get("url", ""),
        checksum=manifest.get("checksum", ""),
        checksum_type=manifest.get("checksum_type", "sha256"),
        release_date=manifest.get("release_date", ""),
        release_notes=manifest.get("release_notes", ""),
        mandatory=manifest.get("mandatory", False),
    )


# ── Download ───────────────────────────────────────────────────────────────────


def _verify_checksum(file_path: Path, expected: str, algo: str = "sha256") -> bool:
    """Return True if the file matches the expected hex digest."""
    try:
        h = hashlib.new(algo)
    except ValueError:
        logger.error("Unsupported checksum algorithm: %s", algo)
        return False

    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)

    actual = h.hexdigest()
    ok = actual == expected.lower()
    if not ok:
        logger.error(
            "Checksum mismatch: expected %s, got %s", expected[:16], actual[:16]
        )
    return ok


def download_update(update: UpdateInfo) -> Optional[Path]:
    """Download the new .exe to a temp directory.

    Returns the path to the downloaded file, or None on failure.
    """
    if not update.url:
        logger.error("Update URL is empty")
        return None

    UPDATE_DIR.mkdir(parents=True, exist_ok=True)
    exe_path = UPDATE_DIR / "pdf_converter.exe"

    # Clean up any partial download from a previous attempt
    if exe_path.exists():
        exe_path.unlink()

    logger.info("Downloading update v%s from %s ...", update.version, update.url)

    try:
        req = Request(update.url, headers={"User-Agent": "pdf_converter-updater/1.0"})
        with urlopen(req, timeout=300) as resp:
            with open(exe_path, "wb") as f:
                # Copy in chunks so we can handle large files
                while chunk := resp.read(65536):
                    f.write(chunk)
    except URLError as e:
        logger.error("Download failed: %s", e)
        return None
    except OSError as e:
        logger.error("IO error during download: %s", e)
        return None

    # Verify checksum if the manifest provided one
    if update.checksum:
        print(f"  Verifying checksum... ", end="", flush=True)
        if not _verify_checksum(exe_path, update.checksum, update.checksum_type):
            print("FAILED")
            exe_path.unlink(missing_ok=True)
            return None
        print("OK")

    logger.info("Update downloaded to %s (%d bytes)", exe_path, exe_path.stat().st_size)
    return exe_path


# ── Apply update ───────────────────────────────────────────────────────────────


def _build_update_bat(
    current_exe: str, new_exe: str, parent_pid: int, restart: bool = True
) -> str:
    """Generate the batch script that replaces the running .exe.

    The script:
      1. Waits for the parent process (``parent_pid``) to exit
      2. Retries ``copy`` until it succeeds (file lock released)
      3. Deletes the downloaded copy
      4. Restarts the updated .exe (optional)
    """
    lines = [
        '@echo off',
        'title pdf_converter - Updating...',
        'echo.',
        'echo ============================================',
        'echo  Updating pdf_converter...',
        'echo ============================================',
        'echo.',
        '',
        ':wait_parent',
        f'tasklist /FI "PID eq {parent_pid}" 2^>NUL | find "{parent_pid}" >NUL',
        'if not errorlevel 1 (',
        '    timeout /t 1 /nobreak >NUL',
        '    goto wait_parent',
        ')',
        '',
        'echo  Replacing file...',
        ':replace',
        f'copy /Y "{new_exe}" "{current_exe}" >NUL',
        'if errorlevel 1 (',
        '    timeout /t 1 /nobreak >NUL',
        '    goto replace',
        ')',
        '',
        'echo  Cleaning up...',
        f'del /F /Q "{new_exe}" >NUL 2>NUL',
        '',
    ]

    if restart:
        lines += [
            'echo  Restarting application...',
            f'start "" "{current_exe}"',
        ]

    lines += [
        '',
        'echo ============================================',
        'echo  Update completed successfully.',
        'echo ============================================',
        'echo.',
        'exit /b 0',
    ]

    return "\r\n".join(lines)


def apply_update(new_exe: Path) -> None:
    """Replace the current executable with the downloaded one.

    This creates ``update.bat`` in the temp directory, launches it,
    and immediately exits the current process.  The batch script
    waits for this process to disappear, replaces the file, and
    optionally restarts.

    Raises ``RuntimeError`` if we are not running as a frozen
    PyInstaller bundle (the update mechanism only works for the
    packaged .exe).
    """
    if not getattr(sys, "frozen", False):
        raise RuntimeError(
            "Apply update is only supported in the packaged .exe. "
            "Run 'python build.spec' first."
        )

    current_exe = sys.executable
    parent_pid = os.getpid()

    UPDATE_DIR.mkdir(parents=True, exist_ok=True)
    batch_path = UPDATE_DIR / "update.bat"

    batch_content = _build_update_bat(
        current_exe=current_exe,
        new_exe=str(new_exe),
        parent_pid=parent_pid,
        restart=True,
    )
    batch_path.write_text(batch_content, encoding="ascii")

    print()
    print("  Applying update...")
    print(f"  Current version: {CURRENT_VERSION}")
    print("  The program will restart automatically.")
    print()

    logger.info(
        "Launching update batch: %s (PID %d → %s)",
        batch_path,
        parent_pid,
        current_exe,
    )

    subprocess.Popen(
        ["cmd", "/c", str(batch_path)],
        shell=True,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )

    # Immediately exit so the batch script can replace the .exe
    sys.exit(0)


# ── Public entry point ─────────────────────────────────────────────────────────


def check_and_apply(manifest_url: Optional[str] = None) -> bool:
    """Convenience: check for an update, download, and apply.

    This is the main entry point called from ``main.py`` when the
    ``--check-update`` flag is used.

    Returns ``True`` if an update was applied (process will exit),
    ``False`` if no update was needed or something failed.
    """
    print()
    print(f"  pdf_converter v{CURRENT_VERSION}")
    print("  Checking for updates...")
    print()

    update = check_for_update(manifest_url)
    if update is None:
        print("  You already have the latest version.")
        print()
        return False

    print(f"  Nuova versione disponibile: v{update.version}")
    if update.release_notes:
        print(f"  What's new: {update.release_notes}")
    print()

    new_exe = download_update(update)
    if new_exe is None:
        print("  ERROR: download failed. Try again later.")
        print()
        return False

    try:
        apply_update(new_exe)
        # Never reached (sys.exit inside apply_update)
    except RuntimeError as e:
        logger.warning("Cannot apply update (dev mode): %s", e)
        print(f"  Update downloaded to: {new_exe}")
        print("  Manually copy the file over the existing one.")
        print()
        return False

    return True  # pragma: no cover (unreachable)
