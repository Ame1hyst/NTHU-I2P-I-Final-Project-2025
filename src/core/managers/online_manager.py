import asyncio
import threading
import time
import queue
import collections
import json
from collections import deque
from typing import Optional
from src.utils import Logger, GameSettings
import requests

try:
    import websockets
except ImportError:
    Logger.error("websockets library not installed. Run: pip install websockets")
    websockets = None

from typing import Any

POLL_INTERVAL = 0.016 # 60Hz Updates

class OnlineManager:
    list_players: list[dict]
    player_id: int
    
    _stop_event: threading.Event
    _fetch_thread: threading.Thread | None
    _send_thread: threading.Thread | None
    _lock: threading.Lock
    _update_queue: queue.Queue
    _session: requests.Session
    
    def __init__(self):
        if websockets is None:
            Logger.error("WebSockets library not available")
            raise ImportError("websockets library required")

        self.base: str = GameSettings.ONLINE_SERVER_URL
        # Convert HTTP URL to WebSocket URL
        if self.base.startswith("http://"):
            self.ws_url = self.base.replace("http://", "ws://")
        elif self.base.startswith("https://"):
            self.ws_url = self.base.replace("https://", "wss://")
        else:
            self.ws_url = f"ws://{self.base}"

        self.player_id = -1
        self.list_players = []
        self._ws = None
        self._ws_loop = None
        self._ws_thread = None
        self._fetch_thread = None 
        self._send_thread = None 
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        
        self._latest_update = None # Use single variable instead of queue
        self._session = requests.Session() # Reuse TCP connection
        
        self._chat_out_queue = queue.Queue(maxsize=50)
        self._chat_messages = deque(maxlen=200)
        self._last_chat_id = 0

        Logger.info("OnlineManager initialized")
        
    def enter(self):
        self.register()
        self.start()
            
    def exit(self):
        self.stop()
        
    def get_list_players(self) -> list[dict]:
        with self._lock:
            return list(self.list_players)

    # ------------------------------------------------------------------
    # Threading and API Calling Below
    # ------------------------------------------------------------------
    def register(self):
        try:
            url = f"{self.base}/register"
            resp = self._session.get(url, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            if resp.status_code == 200:
                self.player_id = data["id"]
                Logger.info(f"OnlineManager registered with id={self.player_id}")
            else:
                Logger.error("Registration failed:", data)
        except Exception as e:
            Logger.warning(f"OnlineManager registration error: {e}")
        return

    def update(self, x: float, y: float, map_name: str, direction = 'down', is_moving = False) -> bool:
        if self.player_id == -1:
            return False
        
        # LIFO: Only keep the LATEST update
        with self._lock:
            self._latest_update = {
                "x": x, 
                "y": y, 
                "map": map_name, 
                "direction": direction, 
                "is_moving": is_moving
            }
        return True

    def start(self) -> None:
        if (self._fetch_thread and self._fetch_thread.is_alive()) or \
           (self._send_thread and self._send_thread.is_alive()):
            return
        
        self._stop_event.clear()
        
        self._fetch_thread = threading.Thread(
            target=self._fetch_loop,
            name="OnlineManagerFetcher",
            daemon=True
        )
        self._fetch_thread.start()
        
        self._send_thread = threading.Thread(
            target=self._send_loop,
            name="OnlineManagerSender",
            daemon=True
        )
        self._send_thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._fetch_thread and self._fetch_thread.is_alive():
            self._fetch_thread.join(timeout=2)
        if self._send_thread and self._send_thread.is_alive():
            self._send_thread.join(timeout=2)

    def _ws_thread_func(self) -> None:
        """Run WebSocket event loop in a separate thread"""
        self._ws_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._ws_loop)
        try:
            self._ws_loop.run_until_complete(self._ws_main())
        except Exception as e:
            Logger.error(f"WebSocket thread error: {e}")
        finally:
            self._ws_loop.close()
            self._ws_loop = None

    def _fetch_loop(self) -> None:
        while not self._stop_event.wait(POLL_INTERVAL):
            self._fetch_players()
    
    def _send_loop(self) -> None:
        while not self._stop_event.is_set():
            data = None
            with self._lock:
                if self._latest_update:
                    data = self._latest_update
                    self._latest_update = None
            
            if data:
                self._send_update(data)
            else:
                time.sleep(POLL_INTERVAL)
            
    def _send_update(self, update_data: dict) -> None:
        if self.player_id == -1:
            return
        
        url = f"{self.base}/players"
        body = {
            "id": self.player_id, 
            **update_data
        }
        
        try:
            # Use session for reusing connection
            resp = self._session.post(url, json=body, timeout=1.0)
            if resp.status_code == 404:
                # Auto-Reconnect
                Logger.warning("PlayerID not found (404). Re-registering...")
                self.register()
            elif resp.status_code != 200:
                Logger.warning(f"Update failed: {resp.status_code}")
        except Exception as e:
            # Logger.warning(f"Update connection error: {e}")
            pass
    
    def _fetch_players(self) -> None:
        if self.player_id == -1:
            return

        url = f"{self.base}/players"
        try:
            resp = self._session.get(url, timeout=1.0)
            if resp.status_code == 200:
                data = resp.json()
                # Server returns dict {id: player_data}, so we need .values()
                players = data.get("players", {}).values()
                
                # Filter out ourselves
                with self._lock:
                    self.list_players = [p for p in players if p["id"] != self.player_id]
        except Exception:
            pass
    
    async def _close_ws(self) -> None:
        """Close WebSocket connection"""
        if self._ws:
            try:
                await self._ws.close()
            except Exception:
                pass
            self._ws = None

    async def _ws_main(self) -> None:
                    await asyncio.sleep(0.5)

    async def _handle_message(self, message: str) -> None:
        """Handle incoming WebSocket message"""
        try:
            data = json.loads(message)
            msg_type = data.get("type")

            if msg_type == "registered":
                self.player_id = int(data.get("id", -1))
                Logger.info(f"OnlineManager registered with id={self.player_id}")

            elif msg_type == "players_update":
                players_data = data.get("players", {})
                with self._lock:
                    filtered = []
                    for pid_str, player_data in players_data.items():
                        pid = int(pid_str)
                        if pid != self.player_id:

                            # HINT: This part might be helpful for direction change
                            # Maybe you can add other parameters?
                            filtered.append({
                                "id": pid,
                                "x": float(player_data.get("x", 0)),
                                "y": float(player_data.get("y", 0)),
                                "map": str(player_data.get("map", "")),
                                "direction": str(player_data.get("direction", "down")),
                                "is_moving": bool(player_data.get("is_moving", False)),
                            })
                    self.list_players = filtered

            elif msg_type == "chat_update":
                messages = data.get("messages", [])
                with self._lock:
                    for m in messages:
                        self._chat_messages.append(m)
                        mid = int(m.get("id", self._last_chat_id))
                        if mid > self._last_chat_id:
                            self._last_chat_id = mid

            elif msg_type == "error":
                Logger.warning(f"Server error: {data.get('message', 'unknown')}")

        except json.JSONDecodeError as e:
            Logger.warning(f"Failed to parse WebSocket message: {e}")
        except Exception as e:
            Logger.warning(f"Error handling WebSocket message: {e}")

    async def _ws_sender(self, websocket: Any) -> None:
        """Send updates to server via WebSocket"""
        update_interval = 0.0167  # 60 updates per second
        last_update = time.monotonic()

        while not self._stop_event.is_set():
            try:
                # Send position updates
                now = time.monotonic()
                if now - last_update >= update_interval:

                    # Drain queue to get latest
                    latest_update = None
                    try:
                        while True:
                            latest_update = self._update_queue.get_nowait()
                    except queue.Empty:
                        pass

                    if latest_update and self.player_id >= 0:
                        # HINT: This part might be helpful for direction change
                        # Maybe you can add other parameters? 
                        message = {
                            "type": "player_update",
                            "x": latest_update.get("x"),
                            "y": latest_update.get("y"),
                            "map": latest_update.get("map"),
                            "direction": latest_update.get("direction", "down"),
                            "is_moving": latest_update.get("is_moving", False)
                        }
                        await websocket.send(json.dumps(message))
                        last_update = now

                # Send chat messages
                try:
                    chat_text = self._chat_out_queue.get_nowait()
                    if self.player_id >= 0:
                        message = {
                            "type": "chat_send",
                            "text": chat_text
                        }
                        await websocket.send(json.dumps(message))
                except queue.Empty:
                    pass

                await asyncio.sleep(0.01)  # Small sleep to prevent busy waiting

            except Exception as e:
                Logger.warning(f"WebSocket send error: {e}")
                await asyncio.sleep(0.1)    
        
    # -----------------------------
    # Chat API
    # -----------------------------
    def send_chat(self, text: str) -> bool:
        if self.player_id == -1:
            return False
        t = (text or "").strip()
        if not t:
            return False
        try:
            self._chat_out_queue.put_nowait(t)
            return True
        except queue.Full:
            return False

    def get_recent_chat(self, limit: int = 50) -> list[dict]:
        with self._lock:
            return list(self._chat_messages)[-limit:]