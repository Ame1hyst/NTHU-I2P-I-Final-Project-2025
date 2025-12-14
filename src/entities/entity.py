from __future__ import annotations
import pygame as pg
from typing import override
from src.sprites import Animation
from src.utils import Position, PositionCamera, Direction, GameSettings
from src.core import GameManager


class Entity:
    animation: Animation
    direction: Direction
    position: Position
    game_manager: GameManager
    
    def __init__(self, x: float, y: float, game_manager: GameManager, img_path: str = 'character/ow1.png') -> None:
        # Sprite is only for debug, need to change into animations
        self.animation = Animation(
            img_path, ["down", "left", "right", "up"], 4,
            (GameSettings.TILE_SIZE, GameSettings.TILE_SIZE)
        )
        self.rect = pg.Rect(x, y, GameSettings.TILE_SIZE, GameSettings.TILE_SIZE)  # For updating rect    
        
        self.position = Position(x, y)
        self.direction = Direction.DOWN
        self.animation.update_pos(self.position)
        self.game_manager = game_manager



    def update(self, dt: float) -> None:
        self.animation.update_pos(self.position)
        self.animation.update(dt)
        
    def draw(self, screen: pg.Surface, camera: PositionCamera, key_press=True) -> None:
        self.animation.draw(screen, camera, key_press)
        if GameSettings.DRAW_HITBOXES:
            self.animation.draw_hitbox(screen, camera)
        
    @staticmethod
    def _snap_to_grid(value: float) -> int:
        return round(value / GameSettings.TILE_SIZE) * GameSettings.TILE_SIZE
    
    @property
    def camera(self) -> PositionCamera:
        position_x = self.animation.rect.centerx - GameSettings.SCREEN_WIDTH//2
        position_y =  self.animation.rect.centery - GameSettings.SCREEN_HEIGHT//2

        # Map size
        map_width = self.game_manager.current_map.tmxdata.width * GameSettings.TILE_SIZE
        map_height = self.game_manager.current_map.tmxdata.height * GameSettings.TILE_SIZE

        # Limit inside map
        self.position.x = max(0, min(position_x, map_width - GameSettings.SCREEN_WIDTH))
        self.position.y = max(0, min(position_y, map_height - GameSettings.SCREEN_HEIGHT))

        return PositionCamera(int(self.position.x), int(self.position.y))
        
    def to_dict(self) -> dict[str, object]:
        return {
            "x": self.position.x / GameSettings.TILE_SIZE,
            "y": self.position.y / GameSettings.TILE_SIZE,
        }
        
    @classmethod
    def from_dict(cls, data: dict[str, float | int], game_manager: GameManager) -> Entity:
        x = float(data["x"])
        y = float(data["y"])
        return cls(x * GameSettings.TILE_SIZE, y * GameSettings.TILE_SIZE, game_manager)
    
    def set_scale(self, scale): #Update RECT
        self.animation.set_scale(scale)
        self.rect.width = self.animation.rect.width
        self.rect.height = self.animation.rect.height