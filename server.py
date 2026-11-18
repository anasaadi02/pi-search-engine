"""Tiny web server. Stdlib only.
GET /             -> index.html
GET /api/search   -> ?mode=digits|date|name&q=...
GET /api/digits   -> ?source=digits|letters&start=1&count=1000  (a window for the viewer)
"""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from search import load_sources, search

SOURCES = load_sources()  # loaded once at startup (~200 MB), shared by every request
MAX_WINDOW = 5000         # never let one request ask for 100 MB
# ponytail: read once; restart server after editing the HTML
PAGE = open("index.html", "rb").read()


class Handler(BaseHTTPRequestHandler):
  def send(self, status, body, content_type):
    self.send_response(status)
    self.send_header("Content-Type", content_type)
    self.send_header("Content-Length", str(len(body)))
    self.end_headers()
    self.wfile.write(body)

  def send_json(self, status, data):
    self.send(status, json.dumps(data).encode(), "application/json")

  def do_GET(self):
    url = urlparse(self.path)
    params = {k: v[0] for k, v in parse_qs(url.query).items()}

    if url.path == "/":
      return self.send(200, PAGE, "text/html; charset=utf-8")

    if url.path == "/api/search":
      try:
        return self.send_json(200, search(SOURCES, params.get("mode", "digits"), params.get("q", "")))
      except ValueError as e:
        return self.send_json(400, {"error": str(e)})  # 400 = "your input was bad", not a crash

    if url.path == "/api/digits":
      data = SOURCES.get(params.get("source", "digits"))
      if data is None:
        return self.send_json(400, {"error": "Unknown source."})
      try:
        start = int(params.get("start", 1))
        count = int(params.get("count", 1000))
      except ValueError:
        return self.send_json(400, {"error": "start and count must be integers."})
      start = min(max(start, 1), len(data))        # clamp into the file
      count = min(max(count, 1), MAX_WINDOW)
      return self.send_json(200, {"start": start, "total": len(data),
                                  "digits": data[start - 1:start - 1 + count]})

    # Only these routes exist on purpose: a generic file server would expose
    # everything in this folder (.venv, config files...).
    self.send(404, b"Not found", "text/plain")


if __name__ == "__main__":
  # 127.0.0.1 = only reachable from this computer. Use "0.0.0.0" to share on your network.
  server = ThreadingHTTPServer(("127.0.0.1", 8000), Handler)
  print("Serving on http://127.0.0.1:8000")
  server.serve_forever()
