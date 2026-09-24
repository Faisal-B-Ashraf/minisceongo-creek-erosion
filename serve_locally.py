"""
Opens the explainer and project assistant on this computer: starts a small local web server for the docs folder
and opens it in the default browser. Use Chrome or Edge to run the in-browser models (they need WebGPU).

usage:  python serve_locally.py [port]        (Ctrl+C to stop)
"""
import functools, http.server, os, socketserver, sys, threading, webbrowser

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")


class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map,
                      ".js": "text/javascript", ".mjs": "text/javascript", ".json": "application/json",
                      ".webp": "image/webp", ".md": "text/markdown; charset=utf-8", ".css": "text/css"}

    def log_message(self, fmt, *args):
        pass


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == "__main__":
    url = f"http://localhost:{PORT}/"
    with Server(("127.0.0.1", PORT), functools.partial(Handler, directory=ROOT)) as httpd:
        print(f"Serving {ROOT}\nOpen {url}  (Ctrl+C to stop)")
        if "--no-browser" not in sys.argv:
            threading.Timer(1.0, lambda: webbrowser.open(url)).start()
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
