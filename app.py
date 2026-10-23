"""Small HTTP server for the statement API and its browser page."""

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from statement import income_statement, load_ledger


ROOT = Path(__file__).resolve().parent


def make_handler(ledger):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            url = urlsplit(self.path)
            if url.path == "/":
                body = (ROOT / "index.html").read_bytes()
                self.respond(200, body, "text/html; charset=utf-8")
            elif url.path == "/income-statement":
                query = parse_qs(url.query, keep_blank_values=True)
                try:
                    start, end = query.get("start", [None]), query.get("end", [None])
                    if len(start) != 1 or len(end) != 1:
                        raise ValueError("Provide one start and one end date")
                    result = income_statement(ledger, start[0], end[0])
                except ValueError as exc:
                    self.json_response(400, {"error": str(exc)})
                    return
                self.json_response(200, result)
            else:
                self.json_response(404, {"error": "Not found"})

        def json_response(self, status, value):
            self.respond(status, json.dumps(value).encode("utf-8"), "application/json; charset=utf-8")

        def respond(self, status, body, content_type):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return Handler


def main():
    ledger = load_ledger(ROOT / "ledger.json")
    port = int(os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer(("127.0.0.1", port), make_handler(ledger))
    print(f"Open http://127.0.0.1:{port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
