"""
pdf_converter - Entry point.

Doppio click  → Avvia server FastAPI + apre browser su localhost:8765
--cli         → Modalita solo backend (CLI tradizionale)
--port NUM    → Porta personalizzata (default 8765)
"""

import argparse
import logging
import sys
import threading
import time
import webbrowser
import uvicorn
import signal

from src.backend.server import app

logger = logging.getLogger("pdf_converter")


def _setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
    )
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)


def _open_browser(port: int) -> None:
    """Aspetta che il server sia pronto e apre il browser."""
    url = f"http://localhost:{port}"
    time.sleep(1.5)
    logger.info("Apro browser a %s ...", url)
    try:
        webbrowser.open(url)
    except Exception:
        logger.warning("Impossibile aprire il browser automaticamente.")


def run_server(port: int) -> None:
    """Avvia il server FastAPI."""
    logger.info("Avvio server pdf_converter su http://localhost:%d", port)
    print(f"\n  Server in ascolto su http://localhost:{port}")
    print(f"  Documentazione API su http://localhost:{port}/docs\n")

    # Thread per aprire browser dopo un attimo
    browser_thread = threading.Thread(
        target=_open_browser, args=(port,), daemon=True
    )
    browser_thread.start()

    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


def run_cli() -> None:
    """Esegue la conversione in modalita CLI tradizionale."""
    from src.backend.main import main as cli_main
    cli_main()


def handle_signal(signum, frame) -> None:
    """Gestisce Ctrl+C con messaggio pulito."""
    print("\n\nChiusura.\n")
    sys.exit(0)


def main() -> None:
    signal.signal(signal.SIGINT, handle_signal)

    parser = argparse.ArgumentParser(
        description="pdf_converter - Convertitore PDF -> Excel",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Esempi:
  main.py              Avvia server web con interfaccia grafica
  main.py --cli        Modalita solo backend (CLI)
  main.py --port 9000  Server su porta 9000
        """,
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Avvia in modalita solo backend (CLI tradizionale)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="Porta per il server web (default: 8765)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Logging dettagliato"
    )
    parser.add_argument(
        "--version", action="version", version="pdf_converter 1.0.0"
    )

    args = parser.parse_args()
    _setup_logging(args.verbose)

    if args.cli:
        run_cli()
    else:
        run_server(args.port)


if __name__ == "__main__":
    main()
