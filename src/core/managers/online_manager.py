import threading
import time
import queue
import collections
import json
from collections import deque
from typing import Optional
from src.utils import Logger, GameSettings
import requests

from typing import Any

POLL_INTERVAL = 0.016 # 60Hz Updates

class OnlineManager:
    list_players: list[dict]
    player_id: int
    
    _stop_event: threading.Event
    _fetch_thread: threading.Thread | None # Two thread to make it faster GET
    _send_thread: threading.Thread | None # POST
    _lock: threading.Lock
    _update_queue: queue.Queue
    _session: requests.Session
    
    def __init__(self):
        self.base: str = GameSettings.ONLINE_SERVER_URL
        self.player_id = -1
        self.list_players = []
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
        # self.register() # MOVED TO BACKGROUND THREAD to prevent lag
        self.start()
            
    def exit(self):
        self.stop()
        
    def get_list_players(self) -> list[dict]:
        with self._lock:
            return list(self.list_players)

    # ------------------------------------------------------------------
    # Threading and API Calling Below
    # ------------------------------------------------------------------
    # ------------------------------------------------------------------
    # Threading and API Calling Below
    # ------------------------------------------------------------------
    def register(self, session: requests.Session = None):
        s = session if session else requests
        try:
            url = f"{self.base}/register"
            resp = s.get(url, timeout=5)
            # resp.raise_for_status() 
            if resp.status_code == 200:
                data = resp.json()
                self.player_id = data["id"]
                Logger.info(f"OnlineManager registered with id={self.player_id}")
            else:
                Logger.warning(f"Registration failed: {resp.status_code}")
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
        # Do not join threads here. It causes lag on scene switch.
        # Threads are daemon and will exit on their own when they see _stop_event.

    def stop(self) -> None:
        self._stop_event.set()
        # Do not join threads here. It causes lag on scene switch.
        # Threads are daemon and will exit on their own when they see _stop_event.

    def _fetch_loop(self) -> None:
        # Create thread-local session
        session = requests.Session()
        
        # Register in background if needed
        if self.player_id == -1:
            self.register(session)
        
        # Counter to throttle chat polling (dont need 60hz)
        tick = 0
        while not self._stop_event.wait(POLL_INTERVAL):
            self._fetch_players(session)
            
            tick += 1
            if tick >= 10: # Fetch chat every 10 frames (~6 times/sec)
                self._fetch_chat(session)
                tick = 0
        
        session.close()
    
    def _send_loop(self) -> None:
        # Create thread-local session
        session = requests.Session()
        
        while not self._stop_event.is_set():
            # 1. Send Position
            data = None
            with self._lock:
                if self._latest_update:
                    data = self._latest_update
                    self._latest_update = None
            if data:
                self._send_update(data, session)
            
            # 2. Send Chat (Drain Queue)
            try:
                while True:
                    text = self._chat_out_queue.get_nowait()
                    self._post_chat(text, session)
            except queue.Empty:
                pass
                
            time.sleep(POLL_INTERVAL)
        
        session.close()
            
    def _post_chat(self, text: str, session: requests.Session):
        if self.player_id == -1: return
        try:
            url = f"{self.base}/chat"
            body = {"id": self.player_id, "text": text}
            session.post(url, json=body, timeout=1.0)
        except Exception:
            pass

    def _send_update(self, update_data: dict, session: requests.Session) -> None:
        if self.player_id == -1:
            return
        
        url = f"{self.base}/players"
        body = {
            "id": self.player_id, 
            **update_data
        }
        
        try:
            # use session for reusing connection
            resp = session.post(url, json=body, timeout=1.0)
            if resp.status_code == 404:
                # Auto-Reconnect
                Logger.warning("PlayerID not found (404). Re-registering...")
                self.register(session)
            elif resp.status_code != 200:
                pass
        except Exception as e:
            # Logger.warning(f"Update connection error: {e}")
            pass
    
    def _fetch_chat(self, session: requests.Session) -> None:
        try:
            url = f"{self.base}/chat"
            resp = session.get(url, timeout=1.0)
            if resp.status_code == 200:
                data = resp.json()
                msgs = data.get("messages", [])
                with self._lock:
                    for m in msgs:
                        mid = int(m.get("id", 0))
                        if mid > self._last_chat_id:
                            self._chat_messages.append(m)
                            self._last_chat_id = mid
        except Exception:
            pass

    def _fetch_players(self, session: requests.Session) -> None:
        if self.player_id == -1:
            return

        url = f"{self.base}/players"
        try:
            resp = session.get(url, timeout=1.0)
            if resp.status_code == 200:
                data = resp.json() # {id: player_data},
                players = data.get("players", {}).values()
                
                with self._lock:
                    self.list_players = [p for p in players if p["id"] != self.player_id] # not including
        except Exception:
            pass
        
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