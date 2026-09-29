import http.server, socketserver

class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        if self.path.endswith(".html") or self.path == "/":
            self.send_header("Content-Type", "text/html; charset=utf-8")
        super().end_headers()

with socketserver.TCPServer(("", 8935), Handler) as httpd:
    httpd.serve_forever()
