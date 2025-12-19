from server.playerHandler import PlayerHandler

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
PORT = 8989
MESSAGES = []

PLAYER_HANDLER = PlayerHandler()
PLAYER_HANDLER.start()
    
class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1" # Enable Keep-Alive

    # def log_message(self, fmt, *args):
    #     return

    def do_GET(self):
        if self.path == "/":
            self._json(200, {"status": "ok"})
            return
            
        if self.path == "/register":
            pid = PLAYER_HANDLER.register()
            self._json(200, {"message": "registration successful", "id": pid})
            return

        if self.path == "/players":
            self._json(200, {"players": PLAYER_HANDLER.list_players()})
            return

        if self.path == "/chat":
            self._json(200, {"messages": MESSAGES})
            return

        self._json(404, {"error": "not_found"})

    def do_POST(self):
        if self.path == "/chat":
            return self.handle_chat_post()
        if self.path == "/players":
            return self.handle_player_update_post()

        # Consuming body is important even for 404 to avoid pipeline corruption
        try:
            length = int(self.headers.get("Content-Length", "0"))
            self.rfile.read(length)
        except: pass
        self._json(404, {"error": "not_found"})

    def handle_player_update_post(self):
        length = int(self.headers.get("Content-Length", "0"))
        try:
            body = self.rfile.read(length)
            data = json.loads(body.decode("utf-8"))
            # Update player data via PLAYER_HANDLER
            # 'update' method needs to exist in PlayerHandler, or we modify dict directly if exposed
            # Assuming PLAYER_HANDLER has an update method or we implement it.
            # Let's check PlayerHandler usage. It seems to wrapper a list/dict.
            # Reigster returns ID.
            # We should probably add update method to PlayerHandler or access its store.
            # For strictness, let's call update. 
            PLAYER_HANDLER.update(
                data["id"],
                data["x"],
                data["y"],
                data["map"],
                data.get("direction", "down"),
                data.get("is_moving", False)
            )
        except Exception as e:
            # print(f"Update error: {e}")
            self._json(400, {"error": "invalid_json"})
            return

        self._json(200, {"success": True})

    def handle_chat_post(self):
        length = int(self.headers.get("Content-Length", "0"))
        try:
            body = self.rfile.read(length)
            data = json.loads(body.decode("utf-8"))
            pid = int(data["id"])
            text = str(data["text"])
        except Exception:
            self._json(400, {"error": "invalid_json"})
            return

        msg = {
            "id": len(MESSAGES) + 1,
            "from": pid,
            "text": text
        }
        MESSAGES.append(msg)
        # Keep only last 50
        if len(MESSAGES) > 50:
            MESSAGES.pop(0)

        self._json(200, {"success": True})

    # Utility for JSON responses
    def _json(self, code: int, obj: object) -> None:
        data = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

if __name__ == "__main__":
    print(f"[Server] Running on localhost with port {PORT}")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
