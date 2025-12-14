from __future__ import annotations
import pygame as pg

from src.sprites import Sprite
from src.core.services import input_manager, resource_manager
from src.utils import Logger
from typing import Callable, override
from .component import UIComponent

class Button(UIComponent):
    img_button: Sprite
    img_button_default: Sprite
    img_button_hover: Sprite
    hitbox: pg.Rect
    on_click: Callable[[], None] | None

    def __init__(
        self,
        img_path: str, img_hovered_path:str,
        x: int, y: int, width: int, height: int,
        on_click: Callable[[], None] | None = None,
        text = None, # for text button
        size: int = 0,
        color = "black"
    ):
        self.img_button_default = Sprite(img_path, (width, height))
        self.img_button_hover = Sprite(img_hovered_path, (width, height))
        self.current_state = self.img_button_default
        
        self.hitbox = pg.Rect(x, y, width, height)

        self.on_click = on_click
        self.is_clicked = False #For Hold the selected img
        self.text_surf = resource_manager.get_font('Minecraft.ttf', size).render(text, True, color) if text else None
        self.text_rect = self.text_surf.get_rect(center = self.hitbox.center) if text else None


    @override
    def update(self, dt: float) -> None:
        if self.hitbox.collidepoint(input_manager.mouse_pos):
            self.current_state = self.img_button_hover
            if input_manager.mouse_pressed(1) and self.on_click is not None:
                self.on_click()
        else:
            self.current_state = self.img_button_default
    
    @override
    def draw(self, screen: pg.Surface) -> None:
        if self.is_clicked:
            surface = self.img_button_hover.image
        else:
            surface = self.current_state.image.copy()
        _ = screen.blit(surface, self.hitbox)
        if self.text_surf:
            screen.blit(self.text_surf, self.text_rect)


def main():
    import sys
    import os
    
    pg.init()

    WIDTH, HEIGHT = 800, 800
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    pg.display.set_caption("Button Test")
    clock = pg.time.Clock()
    
    bg_color = (0, 0, 0)
    def on_button_click():
        nonlocal bg_color
        if bg_color == (0, 0, 0):
            bg_color = (255, 255, 255)
        else:
            bg_color = (0, 0, 0)
        
    button = Button(
        img_path="UI/button_play.png",
        img_hovered_path="UI/button_play_hover.png",
        x=WIDTH // 2 - 50,
        y=HEIGHT // 2 - 50,
        width=100,
        height=100,
        on_click=on_button_click
    )
    
    running = True
    dt = 0
    
    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            input_manager.handle_events(event)
        
        dt = clock.tick(60) / 1000.0
        button.update(dt)
        
        input_manager.reset()
        
        _ = screen.fill(bg_color)
        
        button.draw(screen)
        
        pg.display.flip()
    
    pg.quit()


if __name__ == "__main__":
    main()
