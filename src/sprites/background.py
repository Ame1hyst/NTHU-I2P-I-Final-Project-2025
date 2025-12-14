import pygame as pg

from .sprite import Sprite
from src.utils import GameSettings

class BackgroundSprite(Sprite):
    def __init__(self, image_path: str, size=(GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT), cpos: tuple[int, int] = (0, 0)):
        super().__init__(image_path, size, cpos)
    def draw(self, screen: pg.Surface):
        screen.blit(self.image, self.rect)

    



        
