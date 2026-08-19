"""
StudyFlow — main.py (Web Edition)
Starts Flask on a free port, then opens a pywebview native desktop window.
The old CustomTkinter UI is no longer loaded.
"""

import sys
import os
import threading
import socket
import time
import logging

# Suppress cosmetic warnings:
# 1. pywebview lockfile cleanup — happens when previous session's temp folder lingers
# 2. waitress queue depth — informational noise during burst requests at startup
logging.getLogger('pywebview').setLevel(logging.ERROR)
logging.getLogger('waitress.queue').setLevel(logging.ERROR)

# Ensure project root on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import initialize_database

def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]

def start_flask(port: int):
    """Run Flask via waitress in a daemon thread."""
    from waitress import serve
    from web.app import app
    initialize_database()
    serve(
        app,
        host="127.0.0.1",
        port=port,
        threads=8,           # more threads → queue depth warnings disappear
        connection_limit=100,
        channel_timeout=30,
        cleanup_interval=10,
    )

def main():
    port = find_free_port()

    # Start Flask server in background thread
    flask_thread = threading.Thread(target=start_flask, args=(port,), daemon=True)
    flask_thread.start()

    # Give the server a moment to start
    time.sleep(1.2)

    # Open pywebview window
    import webview

    class Api:
        """JS API bridge exposed to the web page via window.pywebview.api"""
        def open_file_dialog(self):
            # Use the new FileDialog enum (OPEN_DIALOG is deprecated since pywebview 4+)
            result = webview.windows[0].create_file_dialog(
                webview.FileDialog.OPEN, allow_multiple=False
            )
            if result and len(result) > 0:
                return result[0]
            return None

        def open_folder_dialog(self):
            # Use the new FileDialog enum (FOLDER_DIALOG is deprecated since pywebview 4+)
            result = webview.windows[0].create_file_dialog(
                webview.FileDialog.FOLDER
            )
            if result and len(result) > 0:
                return result[0]
            return None

    api = Api()
    window = webview.create_window(
        title="StudyFlow — Your Personal Academic Workspace",
        url=f"http://127.0.0.1:{port}/",
        js_api=api,
        width=1360,
        height=800,
        min_size=(1100, 680),
        text_select=False,
    )
    webview.start(debug=False)


if __name__ == "__main__":
    main()
