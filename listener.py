from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import subprocess
import threading

HOST = "127.0.0.1"
PORT = 8765

codex_running = False

def start_codex():
    global codex_running
    if codex_running:
        print("Codex already running", flush=True)
        return

    codex_running = True
    try:
        subprocess.run(["bash", "run_codex.sh"], check=False)
    finally:
        codex_running = False


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/event":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)

        try:
            payload = json.loads(body.decode("utf-8"))
        except Exception:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"invalid json")
            return

        print("EVENT:", payload, flush=True)

        if payload.get("event") == "assistant_response_complete":
            threading.Thread(target=start_codex, daemon=True).start()

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    print(f"Listening on http://{HOST}:{PORT}", flush=True)
    HTTPServer((HOST, PORT), Handler).serve_forever()
