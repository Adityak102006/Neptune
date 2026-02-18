"""
Neptune Desktop Launcher.
Starts the FastAPI server, opens the browser, and shows a system tray icon.
This is the entry point when running the packaged app.
"""

import sys
import os
import threading
import webbrowser
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Neptune")

HOST = "127.0.0.1"
PORT = 8000
URL = f"http://{HOST}:{PORT}"


def start_server():
    """Start the uvicorn server."""
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=HOST,
        port=PORT,
        log_level="info",
    )


def open_browser_delayed(delay=1.5):
    """Open the browser after a short delay to let the server start."""
    time.sleep(delay)
    webbrowser.open(URL)


def create_tray_icon():
    """Create a system tray icon with Open and Quit options."""
    try:
        import pystray
        from PIL import Image as PilImage, ImageDraw

        # Create a simple Neptune-themed icon (blue circle)
        size = 64
        img = PilImage.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse([4, 4, size - 4, size - 4], fill=(56, 130, 246))
        draw.ellipse([18, 18, size - 18, size - 18], fill=(30, 58, 138))

        def on_open(icon, item):
            webbrowser.open(URL)

        def on_quit(icon, item):
            icon.stop()
            os._exit(0)

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
        icon.run()

    except ImportError:
        logger.info("pystray not available — running without tray icon.")
        logger.info(f"Neptune is running at {URL}")
        logger.info("Press Ctrl+C to quit.")
        # Block main thread so the server keeps running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass


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

    # Open browser after a short delay
    browser_thread = threading.Thread(target=open_browser_delayed, daemon=True)
    browser_thread.start()

    # Run tray icon on the main thread (blocks)
    create_tray_icon()


if __name__ == "__main__":
    main()
