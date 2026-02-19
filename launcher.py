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
import socket
import multiprocessing

# Setup logging to file in APPDATA for debugging
app_data_dir = os.path.join(os.environ.get("APPDATA", ""), "Neptune")
os.makedirs(app_data_dir, exist_ok=True)
log_file = os.path.join(app_data_dir, "neptune.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler(log_file, mode='w'),
        logging.StreamHandler(sys.stdout)
    ]
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


def is_port_in_use(port):
    """Check if port is already in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((HOST, port)) == 0


def start_server():
    """Start the uvicorn server."""
    try:
        logger.info(f"Starting server at {HOST}:{PORT}...")
        
        # Check if port is in use
        if is_port_in_use(PORT):
            logger.warning(f"Port {PORT} is already in use! This might be a zombie process.")
            # We continue anyway, hoping it's a previous instance of Neptune
            # that will respond to our API check.

        import uvicorn
        # Import app object directly (critical for PyInstaller)
        from backend.main import app
        
        # Explicitly disable reload and set workers=1 for frozen app stability
        uvicorn.run(
            app,
            host=HOST,
            port=PORT,
            log_level="info",
            reload=False,
            workers=1,
            access_log=True
        )
    except Exception:
        logger.error("Server crashed:\n%s", traceback.format_exc())


def wait_for_server(timeout=30):
    """Block until the server is accepting connections."""
    import urllib.request
    start = time.time()
    logger.info("Waiting for server to become responsive...")
    
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(f"{URL}/api/version", timeout=1) as response:
                if response.status == 200:
                    logger.info("Server is up and responding!")
                    return True
        except Exception as e:
            # logger.debug(f"Connection check failed: {e}")
            time.sleep(0.5)
            
    logger.error("Server timed out.")
    return False


def open_app_window():
    """
    Open Neptune in a standalone app window using Edge or Chrome --app mode.
    """
    browser_candidates = [
        # Microsoft Edge (Win10/11 default)
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
                    # Allow non-secure connections to localhost
                    "--allow-insecure-localhost", 
                    "--user-data-dir=" + os.path.join(app_data_dir, "edge_profile") # Use separate profile
                ])
                return True
            except Exception:
                logger.warning("Failed to launch %s:\n%s", browser_path, traceback.format_exc())
                continue

    # Fallback
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
    # CRITICAL: Fix for PyInstaller multiprocessing on Windows
    multiprocessing.freeze_support()
    
    logger.info("Neptune launcher starting...")
    logger.info(f"Version: 1.1.4")
    
    # Start server in a background thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # Wait for server to be ready
    if not wait_for_server():
        logger.error("Could not connect to server. Check log for details.")
        # We try to open anyway so the user sees the error
    
    # Open the app
    open_app_window()

    # Run tray icon
    tray = create_tray_icon(lambda: os._exit(0))
    if tray:
        tray.run()
    else:
        logger.info("Running without tray icon. Press Ctrl+C to quit.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
