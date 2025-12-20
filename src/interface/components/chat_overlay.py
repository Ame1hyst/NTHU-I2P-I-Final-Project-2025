from __future__ import annotations
import pygame as pg
from typing import Optional, Callable, List, Dict
from .component import UIComponent
from src.core.services import input_manager, resource_manager
from src.utils import Logger


class ChatOverlay(UIComponent):
    is_open: bool
    _input_text: str
    _cursor_timer: float
    _cursor_visible: bool
    _just_opened: bool
    _send_callback: Callable[[str], bool] | None    #  NOTE: This is a callable function, you need to give it a function that sends the message
    _get_messages: Callable[[int], list[dict]] | None # NOTE: This is a callable function, you need to give it a function that gets the messages
    _font_msg: pg.font.Font
    _font_input: pg.font.Font

    def __init__(
        self,
        send_callback: Callable[[str], bool] | None = None,
        get_messages: Callable[[int], list[dict]] | None = None,
        *,
        font_path: str = "assets/fonts/Minecraft.ttf"
    ) -> None:
        self.is_open = False
        self._input_text = ""
        self._cursor_timer = 0.0
        self._cursor_visible = True
        self._just_opened = False
        self._send_callback = send_callback # sent msg to server
        self._get_messages = get_messages # get msg from server
        self._display_timer = 5
        self._last_seen_msg_id = -1

        try:
            self._font_msg = resource_manager.get_font("Minecraft.ttf", 14)
            self._font_input = resource_manager.get_font("Minecraft.ttf", 18)
        except Exception:
            self._font_msg = pg.font.SysFont("arial", 14)
            self._font_input = pg.font.SysFont("arial", 18)

    def open(self) -> None:
        if not self.is_open:
            self.is_open = True
            self._cursor_timer = 0.0
            self._cursor_visible = True
            self._just_opened = True

    def close(self) -> None:
        self.is_open = False

    def toggle_focus(self) -> None:
        if self.is_open:
            self.close()
        else:
            self.open()

    def _handle_typing(self) -> None:

        shift = input_manager.key_down(pg.K_LSHIFT) or input_manager.key_down(pg.K_RSHIFT)
        
        # A-Z
        for k in range(pg.K_a, pg.K_z + 1):
            if input_manager.key_pressed(k):
                ch = chr(ord('a') + (k - pg.K_a))
                self._input_text += (ch.upper() if shift else ch)
                
        # Space
        if input_manager.key_pressed(pg.K_SPACE):
            self._input_text += " "
            
        # Backspace
        if input_manager.key_pressed(pg.K_BACKSPACE):
            self._input_text = self._input_text[:-1]

        # Numbers/Punctuation (Basic)
        # Add more if needed, for now just basic support
        if input_manager.key_pressed(pg.K_0): self._input_text += "0"
        if input_manager.key_pressed(pg.K_1): self._input_text += "1"
        if input_manager.key_pressed(pg.K_2): self._input_text += "2"
        if input_manager.key_pressed(pg.K_3): self._input_text += "3"
        if input_manager.key_pressed(pg.K_4): self._input_text += "4"
        if input_manager.key_pressed(pg.K_5): self._input_text += "5"
        if input_manager.key_pressed(pg.K_6): self._input_text += "6"
        if input_manager.key_pressed(pg.K_7): self._input_text += "7"
        if input_manager.key_pressed(pg.K_8): self._input_text += "8"
        if input_manager.key_pressed(pg.K_9): self._input_text += "9"

        # Enter to send
        if input_manager.key_pressed(pg.K_RETURN) or input_manager.key_pressed(pg.K_KP_ENTER):
            txt = self._input_text.strip()
            if txt and self._send_callback:
                ok = False
                try:
                    ok = self._send_callback(txt)
                except Exception:
                    ok = False
                if ok:
                    self._input_text = ""


    def update(self, dt: float) -> None:
        # Check for new messages to reset timer
        if self._get_messages:
            current_msgs = self._get_messages(1) # check last one
            if current_msgs:
                pass
        
        if self.is_open:
            self._display_timer = 30.0
        else:
            if self._display_timer > 0:
                self._display_timer -= dt

        if not self.is_open:
            return

        # Close on Escape (Changed from X to Escape)
        if input_manager.key_pressed(pg.K_ESCAPE):
            self.close()
            return

        # Typing
        if self._just_opened:
            self._just_opened = False
        else:
            self._handle_typing()
        
        # Cursor blink
        self._cursor_timer += dt
        if self._cursor_timer >= 0.5:
            self._cursor_timer = 0.0
            self._cursor_visible = not self._cursor_visible

    def draw(self, screen: pg.Surface) -> None:
        msgs = self._get_messages(3) if self._get_messages else [] # get last 3 message
        
        # check new msg to reset timer
        if msgs:
            last_msg = msgs[-1]
            last_id = int(last_msg.get("id", -1))
            if last_id != self._last_seen_msg_id:
                self._display_timer = 5
                self._last_seen_msg_id = last_id
        
        # draw recent msg
        if self.is_open or self._display_timer > 0:
            sw, sh = screen.get_size()
            container_w = max(100, int((sw - 20) * 0.4))
            
            # padding
            x = 10
            y = sh - 100
            
            # msg background
            if msgs:
                alpha = 90 if self.is_open else 60
                
                bg = pg.Surface((container_w, 90), pg.SRCALPHA)
                bg.fill((0, 0, 0, alpha))
                _ = screen.blit(bg, (x, y))
                # Render last messages
                lines = list(msgs)[-3:]
                draw_y = y + 8
                for m in lines:
                    sender = str(m.get("from", ""))
                    text = str(m.get("text", ""))
                    surf = self._font_msg.render(f"{sender}: {text}", True, (255, 255, 255))
                    _ = screen.blit(surf, (x + 10, draw_y))
                    draw_y += surf.get_height() + 4
                    
        # If not open, skip input field
        if not self.is_open:
            return
        # Input box
        box_h = 28
        box_w = max(100, int((sw - 20) * 0.6))
        box_y = sh - box_h - 6
        
        # Background box       
        bg2 = pg.Surface((box_w, box_h), pg.SRCALPHA)
        bg2.fill((0, 0, 0, 160))
        _ = screen.blit(bg2, (x, box_y))
        
        # Text
        txt = self._input_text
        text_surf = self._font_input.render(txt, True, (255, 255, 255))
        _ = screen.blit(text_surf, (x + 8, box_y + 4))
        if self._cursor_visible:
            cx = x + 8 + text_surf.get_width() + 2
            cy = box_y + 6
            pg.draw.rect(screen, (255, 255, 255), pg.Rect(cx, cy, 2, box_h - 12))
