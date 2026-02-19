"""
Neptune Desktop Launcher.
Starts the FastAPI server and opens a dedicated app window (via Edge/Chrome app mode).
Shows a system tray icon for quick access and quitting.
This is the entry point when running the packaged app.
"""

import sys
import os
import subprocess
import threading
import time
import logging
import traceback

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("Neptune")

HOST = "127.0.0.1"
PORT = 8000
URL = f"http://{HOST}:{PORT}"


def _get_asset_path(filename):
    """Resolve path to a bundled asset file (works for dev and PyInstaller)."""
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "assets", filename)


def start_server():
    """Start the uvicorn server."""
    try:
        import uvicorn
        from backend.main import app
        uvicorn.run(
            app,
            host=HOST,
            port=PORT,
            log_level="info",
        )
    except Exception:
        logger.error("Server crashed:\n%s", traceback.format_exc())


def wait_for_server(timeout=20):
    """Block until the server is accepting connections."""
    import urllib.request
    start = time.time()
    while time.time() - start < timeout:
        try:
            urllib.request.urlopen(f"{URL}/api/version", timeout=2)
            return True
        except Exception:
            time.sleep(0.5)
    return False


def open_app_window():
    """
    Open Neptune in a standalone app window using Edge or Chrome --app mode.
    This removes the address bar, tabs, and browser chrome so it looks
    like a native desktop application. Edge is pre-installed on Windows 10/11.
    Falls back to the default browser if neither Edge nor Chrome is found.
    """
    # Possible browser paths on Windows (Edge is always available on Win10/11)
    browser_candidates = [
        # Microsoft Edge (most reliable — pre-installed on Windows 10/11)
        os.path.join(os.environ.get("ProgramFiles(x86)", ""), "Microsoft", "Edge", "Application", "msedge.exe"),
        os.path.join(os.environ.get("ProgramFiles", ""), "Microsoft", "Edge", "Application", "msedge.exe"),
        # Google Chrome
        os.path.join(os.environ.get("ProgramFiles(x86)", ""), "Google", "Chrome", "Application", "chrome.exe"),
        os.path.join(os.environ.get("ProgramFiles", ""), "Google", "Chrome", "Application", "chrome.exe"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google", "Chrome", "Application", "chrome.exe"),
    ]

    for browser_path in browser_candidates:
        if browser_path and os.path.isfile(browser_path):
            logger.info("Opening app window with: %s", browser_path)
            try:
                subprocess.Popen([
                    browser_path,
                    f"--app={URL}",
                    "--new-window",
                    "--disable-extensions",
                    "--disable-default-apps",
                ])
                return True
            except Exception:
                logger.warning("Failed to launch %s:\n%s", browser_path, traceback.format_exc())
                continue

    # Fallback: open in default browser (with normal browser chrome)
    logger.warning("No Edge/Chrome found — falling back to default browser.")
    import webbrowser
    webbrowser.open(URL)
    return False


def create_tray_icon(on_quit_callback):
    """Create a system tray icon with Open and Quit options."""
    try:
        import pystray
        from PIL import Image as PilImage

        icon_path = _get_asset_path("neptune.png")
        if os.path.isfile(icon_path):
            img = PilImage.open(icon_path)
            img = img.resize((64, 64), PilImage.LANCZOS)
        else:
            from PIL import ImageDraw
            size = 64
            img = PilImage.new("RGBA", (size, size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.ellipse([4, 4, size - 4, size - 4], fill=(56, 130, 246))
            draw.ellipse([18, 18, size - 18, size - 18], fill=(30, 58, 138))

        def on_open(icon, item):
            open_app_window()

        def on_quit(icon, item):
            icon.stop()
            on_quit_callback()

        icon = pystray.Icon(
            "Neptune",
            img,
            "Neptune — Image Search",
            menu=pystray.Menu(
                pystray.MenuItem("Open Neptune", on_open, default=True),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Quit", on_quit),
            ),
        )
        return icon

    except Exception:
        logger.warning("Tray icon not available:\n%s", traceback.format_exc())
        return None


def main():
    print(f"""
    ╔══════════════════════════════════════════╗
    ║       🔱  N E P T U N E                 ║
    ║    Local Image Similarity Search         ║
    ╚══════════════════════════════════════════╝

    Server: {URL}
    """)

    # Start server in a background thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # Wait for server to be ready
    logger.info("Waiting for server to start...")
    if not wait_for_server():
        logger.error("Server failed to start within timeout.")
        logger.info("Attempting to open anyway...")
    else:
        logger.info("Server is ready!")

    # Open the app in a standalone window (Edge/Chrome --app mode)
    open_app_window()

    # Run tray icon on the main thread (blocks until Quit)
    tray = create_tray_icon(lambda: os._exit(0))
    if tray:
        tray.run()
    else:
        # No tray icon — keep alive via console
        logger.info(f"Neptune is running at {URL}")
        logger.info("Press Ctrl+C to quit.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
