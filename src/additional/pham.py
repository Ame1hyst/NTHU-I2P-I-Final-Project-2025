from src.utils import Position, GameSettings, PositionCamera
from src.core.services import resource_manager, input_manager, scene_manager
import pygame as pg
class Pham:
    def __init__(self, id: str, pos: Position, img_path: str = "krajua/pham.png"):
        self.id = id
        self.pos = pos        
        self.img = resource_manager.get_image(img_path, (100, 100),) 
    
    @property
    def rect(self):
        return pg.Rect((self.pos.x, self.pos.y), self.img.get_size())
    
    def draw(self, screen: pg.Surface, camera: PositionCamera):
        screen.blit(self.img, camera.transform_rect(self.rect))
    
    @classmethod
    def from_dict(cls, data: dict) -> "Pham":
        return cls(
            id=data["id"],
            pos=Position(data["x"] * GameSettings.TILE_SIZE, data["y"] * GameSettings.TILE_SIZE),
            img_path=data.get("img_path", "krajua/pham.png")
        )