import pygame as pg

from src.utils import GameSettings
from src.sprites import BackgroundSprite
from src.scenes.scene import Scene
from src.interface.components import Button
from src.core.managers import GameManager, AchieveManager
from src.core.services import scene_manager, sound_manager, input_manager, resource_manager
from src.interface.components.dialog import Dialog
from src.sprites.animation import Animation
from typing import override


class AchievementSCene(Scene):
    def __init__(self):
        self.game_manager = GameManager.get_instance()
        self.ui_setup()
        
        am_manager = AchieveManager()
        self.achievement_data = am_manager.achievement_data

        self.img_render = []
        self.sheet_ani = {}
        self.current_rect = None
        self.current_animation = None
        self.hovered_achievement = None

    @property
    def progress(self):
        return self.game_manager.achievement

    def ui_setup(self):
        #Button asset setup
        self.background = BackgroundSprite("krajua/stamp_banner.png", size=(GameSettings.SCREEN_WIDTH*0.75, GameSettings.SCREEN_HEIGHT*0.8), cpos=(GameSettings.SCREEN_WIDTH *0.13, GameSettings.SCREEN_HEIGHT* 0.1))
        self.x_button = Button(
            "UI/button_x.png", "UI/button_x_hover.png",
            self.background.rect.right-60, self.background.rect.top +20, 35, 35,
            lambda: scene_manager.change_scene(scene_manager.previous_screen_name))

        self.large_font = resource_manager.get_font('Minecraft.ttf', 20)
        self.mid_font = resource_manager.get_font('Minecraft.ttf', 15)
        self.small_font = resource_manager.get_font('Minecraft.ttf', 10)

        #Text warning
        self.dialog_surf = resource_manager.get_image('krajua/text_banner02.png',(200, 60))
        self.dialog_rect = None
        self.dialog = None

    
  
    @override
    def enter(self) -> None:
        sound_manager.play_sound('open-bag-sound.mp3')
        self.render_achieve_pic()
       
    @override
    def exit(self) -> None:
        sound_manager.play_sound('open-bag-sound.mp3')
        self.reset()
        
    @override
    def update(self, dt: float):
        self.x_button.update(dt)
   
        hovered_rect = None # For one time render
        self.hovered_achievement = None
        
        for achievement, _, rect in self.img_render:
            if rect.collidepoint(input_manager.mouse_pos):
                hovered_rect = rect
                self.hovered_achievement = achievement
                self.current_animation = self.sheet_ani[achievement]
                break
        else:
            self.reset()

        if hovered_rect != self.current_rect:
                self.current_rect = hovered_rect
                if self.hovered_achievement:
                    self.current_animation = self.sheet_ani[self.hovered_achievement]
                    self.current_animation.rect = hovered_rect #set rect pos
                    self.render_text(self.hovered_achievement, self.current_rect)
                else:
                    self.current_animation = None
                    self.dialog = None

        if self.current_animation and self.hovered_achievement in self.progress.get("unlocked", []):
            self.current_animation.update(dt)
        
        if self.dialog and self.dialog.current_text:
            self.dialog.update(dt)
    
    @override
    def draw(self, screen: pg.Surface):
        screen.blit(scene_manager.previous_screen_surf, (0,0))
        overlay = pg.Surface((screen.get_size()), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        screen.blit(overlay, (0,0))
        
        self.background.draw(screen)

        self.x_button.draw(screen)

        
        for achievement, img, rect in self.img_render:
            if achievement in self.progress.get("unlocked", []) and achievement != self.hovered_achievement:
                screen.blit(img, rect)
                
            if GameSettings.DRAW_HITBOXES:
                pg.draw.rect(screen, "red", rect, 2)
       
        if self.current_animation and self.hovered_achievement in self.progress.get("unlocked", []):
            self.current_animation.draw(screen)

        self.draw_text(screen)
       
    
    def render_text(self, achievement, rect):
        self.dialog_rect = self.dialog_surf.get_rect(midbottom=(rect.right + 5 , rect.centery))
        
        self.dialog = Dialog(self.dialog_rect, (20,15), speed=20, size=15, color="Black",)
        
        unlocked = achievement in  self.progress.get("unlocked", [])
        data = self.achievement_data[achievement]
        if unlocked:
            text = data['hint_unlocked'] 
        else:
            if achievement in self.progress.keys() and achievement != "boss_defeated" and self.progress.get(achievement, 0):
                progress_val = self.progress.get(achievement)
                count = len(progress_val) if isinstance(progress_val, list) else progress_val
                text = f"Now get {count}{data['hint_progress']}"
            
            else:
                 text = data['hint_locked']
        
        if not self.dialog.current_text:
            self.dialog.add_sequence(text)     

        
    
    def draw_text(self, screen,):
        if not self.dialog or not self.current_rect:
            return            
        screen.blit(self.dialog_surf, self.dialog_rect)
        self.dialog.draw(screen)


    def render_achieve_pic(self):
        self.img_render.clear()
        self.sheet_ani.clear()
        for achievement, data in self.achievement_data.items():
            img = resource_manager.get_image(data['sprite_path'])
            img = pg.transform.scale(img, (200, 200))
            x, y = data['pos']
            rect = img.get_rect(center=(x, y))
            self.img_render.append((achievement, img, rect))
        
            sheet_path, sprite_num = data['sheet']
            self.sheet_ani[achievement] = Animation(
                sheet_path, ['animation'], sprite_num, (200, 200)
            )

      
    
    def reset(self):
        self.current_rect = None
        self.current_animation = None
        self.dialog = None