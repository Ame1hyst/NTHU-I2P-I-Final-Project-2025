import pygame as pg
from src.core.services import resource_manager
from src.utils import Position, PositionCamera
from typing import Optional

class Sprite:
    image: pg.Surface
    rect: pg.Rect
    
    def __init__(self, img_path: str, size: tuple[int, int] | None = None, cpos: tuple[int, int] = (0, 0)):
        self.o_image = resource_manager.get_image(img_path)
        if size is not None:
            self.o_image = pg.transform.scale(self.o_image, size)
        self.image = self.o_image.copy()
        self.rect = self.image.get_rect(topleft=(cpos)) # Change pos

        self.scale = 1.0
        
    def set_scale(self, scale):
        self.scale = scale

        o_width, o_height = self.o_image.get_size()
        n_width, n_height = o_width*self.scale, o_height*self.scale

        self.image = pg.transform.scale(self.image, (n_width, n_height))

        o_cpos = self.rect.topleft
        self.rect = self.image.get_rect(topleft=o_cpos) 
        
    def update(self, dt: float):
        pass

    def draw(self, screen: pg.Surface, camera: Optional[PositionCamera] = None):
        if camera is not None:
            screen.blit(self.image, camera.transform_rect(self.rect))
        else:
            screen.blit(self.image, self.rect)
        
    def draw_hitbox(self, screen: pg.Surface, camera: Optional[PositionCamera] = None):
        if camera is not None:
            pg.draw.rect(screen, (255, 0, 0), camera.transform_rect(self.rect), 1) #close wide
        else:
            pg.draw.rect(screen, (255, 0, 0), self.rect, 1)
        
    def update_pos(self, pos: Position):
        self.rect.topleft = (round(pos.x), round(pos.y))