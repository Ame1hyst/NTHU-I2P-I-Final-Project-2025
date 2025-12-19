from __future__ import annotations
import pygame as pg
from .entity import Entity
from src.core.services import input_manager, scene_manager
from src.utils import Position, PositionCamera, Direction, GameSettings, Logger
from src.core import GameManager
import math
from typing import override

class Player(Entity):
    speed: float = 4.0 * GameSettings.TILE_SIZE
    game_manager: GameManager

    def __init__(self, x: float, y: float, game_manager: GameManager) -> None:
        super().__init__(x, y, game_manager)
        self.speed
        self.x = x
        self.y = y
        self.game_manager = game_manager
        self.direction = Direction.NONE


    @override
    def update(self, dt: float) -> None:
        #Input walk + facing
        dis = Position(0, 0)
        if input_manager.key_down(pg.K_LEFT) or input_manager.key_down(pg.K_a):
            dis.x -= 1
            self.animation.switch('left')
            self.direction = "left"
        if input_manager.key_down(pg.K_RIGHT) or input_manager.key_down(pg.K_d):
            dis.x += 1
            self.animation.switch('right')
            self.direction = "right"
        if input_manager.key_down(pg.K_UP) or input_manager.key_down(pg.K_w):
            dis.y -= 1
            self.animation.switch('up')
            self.direction = "up"
        if input_manager.key_down(pg.K_DOWN) or input_manager.key_down(pg.K_s):
            dis.y += 1
            self.animation.switch('down')
            self.direction = "down"
        
        #Normalize
        length = (dis.x**2 + dis.y**2)**(0.5)
        if length:
            dis.x, dis.y = dis.x/length, dis.y/length
        #Calculate
        self.x += dis.x*self.speed*dt
        self.rect.x = self.x
        if self.game_manager.check_collision(self.rect):
            self.x = Entity._snap_to_grid(self.x)
            self.rect.x = self.x  
        
        self.y += dis.y*self.speed*dt
        self.rect.y = self.y
        if self.game_manager.check_collision(self.rect):
            self.y = Entity._snap_to_grid(self.y)
            self.rect.y = self.y 
        self.position = Position(self.x, self.y)
        
        # Check teleportation
        tp = self.game_manager.current_map.check_teleport(self.position)
        if tp:
            self.game_manager.switch_map(tp)
        super().update(dt)

        #Check Bush
        if self.game_manager.check_bush(self.rect) and input_manager.key_pressed(pg.K_SPACE):
            scene_manager.change_scene('selected_pokemon')

    @override
    def draw(self, screen: pg.Surface, camera: PositionCamera) -> None:
        movement_keys = [pg.K_LEFT, pg.K_RIGHT, pg.K_UP, pg.K_DOWN, pg.K_a, pg.K_d, pg.K_s, pg.K_w]    
        super().draw(screen, camera, key_press=any(input_manager.key_down(key) for key in movement_keys))
        
    @override
    def to_dict(self) -> dict[str, object]:
        return super().to_dict()
    
    @classmethod
    @override
    def from_dict(cls, data: dict[str, object], game_manager: GameManager) -> Player:
        return cls(data["x"] * GameSettings.TILE_SIZE, data["y"] * GameSettings.TILE_SIZE, game_manager)
    

