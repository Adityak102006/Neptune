"""
Neptune Desktop Launcher.
Starts the FastAPI server and opens a native desktop window using pywebview.
Falls back to the browser if pywebview is not available.
This is the entry point when running the packaged app.
"""

import sys
import os
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
        # Running as a PyInstaller bundle
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "assets", filename)


def start_server():
    """Start the uvicorn server."""
    try:
        import uvicorn
        uvicorn.run(
            "backend.main:app",
            host=HOST,
            port=PORT,
            log_level="info",
        )
    except Exception:
        logger.error("Server crashed:\n%s", traceback.format_exc())


def wait_for_server(timeout=20):
    """Block until the server is accepting connections."""
    import urllib.request
    import urllib.error
    start = time.time()
    while time.time() - start < timeout:
        try:
            urllib.request.urlopen(f"{URL}/api/version", timeout=2)
            return True
        except Exception:
            time.sleep(0.5)
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
            import webbrowser
            webbrowser.open(URL)

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
        # run_detached runs the tray icon in a separate thread
        tray_thread = threading.Thread(target=icon.run, daemon=True)
        tray_thread.start()
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
        # Still try to open — server might just be slow
        logger.info("Attempting to open anyway...")

    logger.info("Server is ready!")

    # Try to open in a native webview window
    try:
        import webview

        logger.info("pywebview found — launching native window...")

        def on_closed():
            """Called when the webview window is closed."""
            logger.info("Window closed. Shutting down...")
            os._exit(0)

        # Create tray icon that can quit the app
        tray = create_tray_icon(lambda: os._exit(0))

        # Create the native window
        window = webview.create_window(
            "Neptune — Image Search",
            URL,
            width=1280,
            height=800,
            min_size=(900, 600),
            resizable=True,
            text_select=True,
        )
        window.events.closed += on_closed

        # Start webview — let pywebview pick the best available backend
        # Do NOT force gui="edgechromium" as it may not be available
        webview.start()

    except ImportError:
        logger.warning("pywebview not installed — falling back to browser.")
        _fallback_browser()
    except Exception:
        logger.error("pywebview failed:\n%s", traceback.format_exc())
        logger.info("Falling back to browser...")
        _fallback_browser()


def _fallback_browser():
    """Open in the system browser and keep the process alive."""
    import webbrowser
    webbrowser.open(URL)

    tray = create_tray_icon(lambda: os._exit(0))
    if tray is None:
        logger.info(f"Neptune is running at {URL}")
        logger.info("Press Ctrl+C to quit.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
    else:
        # Keep main thread alive while tray is running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
