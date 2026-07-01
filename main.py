"""
pdf_converter - Entry point.

Double-click  -> Launches FastAPI server and opens browser at localhost:8765
--cli         -> Backend-only mode (traditional CLI)
--port NUM    -> Custom port (default: 8765)
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
from tools.updater.update_router import router as update_router

app.include_router(update_router)

logger = logging.getLogger("pdf_converter")


def _setup_logging(verbose: bool = False) -> None:
    """Configure logging level and format.

    Sets DEBUG level when verbose is True, otherwise INFO.
    Suppresses verbose uvicorn access logs.

    Args:
        verbose: Enable debug-level logging when True.
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
    )
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)


def _open_browser(port: int) -> None:
    """Wait for the server to be ready and open the browser.

    Args:
        port: The port the server is listening on.
    """
    url = f"http://localhost:{port}"
    time.sleep(1.5)
    logger.info("Opening browser at %s ...", url)
    try:
        webbrowser.open(url)
    except Exception:
        logger.warning("Could not open browser automatically.")


def run_server(port: int) -> None:
    """Start the FastAPI server.

    Args:
        port: The port to bind the server to.
    """
    logger.info("Starting pdf_converter server on http://localhost:%d", port)
    print(f"\n  Server listening on http://localhost:{port}")
    print(f"  API documentation at http://localhost:{port}/docs\n")

    # Thread to open browser after a short delay
    browser_thread = threading.Thread(
        target=_open_browser, args=(port,), daemon=True
    )
    browser_thread.start()

    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


def run_cli() -> None:
    """Run the conversion in traditional CLI mode."""
    from src.backend.main import main as cli_main
    cli_main()


def handle_signal(signum, frame) -> None:
    """Handle Ctrl+C with a clean shutdown message.

    Args:
        signum: Signal number.
        frame: Current stack frame.
    """
    print("\n\nShutdown.\n")
    sys.exit(0)


def main() -> None:
    signal.signal(signal.SIGINT, handle_signal)

    parser = argparse.ArgumentParser(
        description="pdf_converter - PDF to Excel Converter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  main.py                        Start web server with GUI
  main.py --cli                  Backend-only mode (CLI)
  main.py --port 9000            Server on port 9000
  main.py --check-update         Check for updates on startup
        """,
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Start in backend-only mode (traditional CLI)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="Port for the web server (default: 8765)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Detailed logging"
    )
    parser.add_argument(
        "--version", action="version", version="pdf_converter 2.0.0"
    )
    parser.add_argument(
        "--check-update",
        action="store_true",
        help="Check for updates on startup",
    )
    parser.add_argument(
        "--update-manifest-url",
        type=str,
        default=None,
        help=argparse.SUPPRESS,  # Advanced option, hidden from --help
    )

    args = parser.parse_args()
    _setup_logging(args.verbose)

    # -- Auto-update check --------------------------------------------------------
    if args.check_update:
        from tools.updater.updater import check_for_update, do_update

        available, latest, release = check_for_update()
        if available:
            do_update(release)
            return  # Process will exit via sys.exit inside do_update

    # -- Normal startup -----------------------------------------------------------
    if args.cli:
        run_cli()
    else:
        run_server(args.port)


if __name__ == "__main__":
    main()
