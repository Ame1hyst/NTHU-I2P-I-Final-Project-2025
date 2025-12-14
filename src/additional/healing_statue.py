import pygame as pg
from src.core.managers import GameManager
from src.core.services import resource_manager, input_manager, scene_manager
from src.utils import PositionCamera, GameSettings
from src.interface.components.dialog import Dialog

class HealStatue():
    def __init__(self, x, y, img_path):
        self.statue_img = resource_manager.get_image(img_path, (100, 100))
        
        pos_x = x * GameSettings.TILE_SIZE
        pos_y = y* GameSettings.TILE_SIZE
        self.statue_rect = self.statue_img.get_rect(topleft = (pos_x, pos_y))

        #Text warning
        self.dialog_surf = resource_manager.get_image('krajua/text_banner.png',(200, 60))
        self.dialog_rect = self.dialog_surf.get_rect(midbottom = (self.statue_rect.right, self.statue_rect.top - 5))
        self.dialog = Dialog(self.dialog_rect, (35, 10), speed=20, size=15, color="Black",)
    
    def draw(self, screen, camera: PositionCamera):
        if not self.statue_img:
            return

        screen.blit(self.statue_img, camera.transform_rect(self.statue_rect))

        if self.dialog.current_text:
            screen.blit(self.dialog_surf,  camera.transform_rect(self.dialog_rect))
            self.dialog.rect = self.dialog_rect
            self.dialog.draw(screen, camera)
        
        if GameSettings.DRAW_HITBOXES:
            pg.draw.rect(screen, (255, 0, 0), camera.transform_rect(self.statue_rect), 1)
    
    def update(self, dt, player):       
        if not self.statue_rect:
            return        
                    
        if self.statue_rect.colliderect(player.rect):
            if not self.dialog.current_text:
                self.dialog.add_sequence("Play to HEAL ALL")     
        else:
            if self.dialog.current_text or self.dialog.queue:
                self.dialog.reset()
            
        if self.dialog.current_text:
            self.dialog.update(dt)
            
            if input_manager.key_pressed(pg.K_SPACE):
                scene_manager.change_scene('minigame')


