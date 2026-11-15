import http.server
import json

RATES = {"base": "USD", "rates": {"GBP": 0.77, "EUR": 0.91, "BRL": 5.0, "JPY": 150.0, "TRY": 32.0}}


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        body = json.dumps(RATES).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    http.server.HTTPServer(("127.0.0.1", 8000), Handler).serve_forever()