import pygame as pg
from src.utils import GameSettings
from src.scenes.scene import Scene
from src.sprites import BackgroundSprite
from src.interface.components import Button
from src.core.managers import GameManager, AchieveManager
from src.core.services import scene_manager, sound_manager, input_manager, resource_manager
from typing import override
import random

class MiniGame(Scene):
    def __init__(self):
        super().__init__()
        self.game_manager = None
        self.achievement_manager = AchieveManager()
        self.state = "show"
        self.healed = False

        #Timer set up
        self.time_start = 0
        self.ani_timer = 0
        self.time_limited = 30
        self.speed = 10

        #Game set
        self.correct = 0
        self.chance = 3
        self.ran_direction = []
        self.q_direction = []
        self.input_direction = []
        self.directon = ['up', 'down', 'left', 'right']
        
        img = resource_manager.get_image('krajua/prai_sheet.png')
        sheet_w, sheet_h = img.get_size()
        frame_w = sheet_w // 4
        size = (100, 150)
        self.ani_idx = 0
        self.animation_surfs = {
            'up':    pg.transform.smoothscale(img.subsurface((0, 0, frame_w,  sheet_h)), size),
            'left':  pg.transform.smoothscale(img.subsurface((frame_w, 0, frame_w,  sheet_h)), size),
            'down':  pg.transform.smoothscale(img.subsurface((frame_w*2, 0, frame_w,  sheet_h)), size),
            'right': pg.transform.smoothscale(img.subsurface((frame_w*3, 0, frame_w,  sheet_h)), size),
        }
        

        self.ui_setup()    
    
    def ui_setup(self):
        #Button asset setup
        self.background = BackgroundSprite("krajua/mini_background.png", size=(GameSettings.SCREEN_WIDTH*0.95, GameSettings.SCREEN_HEIGHT*0.9), cpos=(GameSettings.SCREEN_WIDTH *0.05, GameSettings.SCREEN_HEIGHT* 0.01))
        self.x_button = Button(
            "UI/button_x.png", "UI/button_x_hover.png",
            self.background.rect.topleft[0]+140, self.background.rect.topleft[1]+160, 35, 35,
            lambda: scene_manager.change_scene(scene_manager.previous_screen_name))
        
        
        self.extra_large = resource_manager.get_font('Minecraft.ttf', 40)
        self.large_font = resource_manager.get_font('Minecraft.ttf', 20)
        self.mid_font = resource_manager.get_font('Minecraft.ttf', 15)
        self.small_font = resource_manager.get_font('Minecraft.ttf', 10)

        self.title_surf = self.extra_large.render(f"Press as show", True, "#251C1C")
        self.title_rect = self.title_surf.get_rect(center = (self.background.rect.centerx-50, self.background.rect.top+350))

    @override
    def enter(self):
        self.game_manager = GameManager.get_instance()
        self.get_ran_direction()

    @override
    def update(self, dt):
        self.x_button.update(dt)
        self.handle_state(dt)


    @override
    def draw(self, screen):
        screen.blit(scene_manager.previous_screen_surf, (0,0))
        overlay = pg.Surface((screen.get_size()), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        screen.blit(overlay, (0,0))
        
        self.background.draw(screen)
        self.x_button.draw(screen)

        if self.state == 'show':
            self.draw_ran_img(screen)
        elif self.state == 'input':
            self.draw_player_input(screen)
        elif self.state == 'wrong':
            if self.chance >= 0:
                self.text_output(screen, f"Wrong Ans! {self.chance} chance Letf")
            else:
                self.text_output(screen, f"GAME OVER")
        elif self.state == 'correct':
            if not self.correct >= 4:
                self.text_output(screen, f"Correct Answer")
            else:
                self.text_output(screen, f"Pass ALL")
        
        if not self.state == 'over':
            screen.blit(self.title_surf, self.title_rect)
        else:
            from src.core.managers.autosave_manager import AutoSaveManager
            auto_save = AutoSaveManager(self.game_manager)
            if self.correct >= 4:
                self.text_output(screen, f"HEAL ALL POKEMON")
                surf =list(self.animation_surfs.values())[self.ani_idx]
                rect = surf.get_rect(center=self.background.rect.center)
                screen.blit(surf, (rect.x-50, rect.y))
                

                if  not self.healed:
                    self.game_manager.bag.heal_all()
                    auto_save.force_save()
                    self.achievement_manager.add_heal_count()
                    self.healed = True
                
                    
    @override
    def exit(self):
        self.reset()

    
    def handle_state(self, dt):
        if self.state == 'show':
            if not self.ran_direction:
                self.time_limited = 30 - (self.correct*5)
                self.get_ran_direction()

            else:
                if not self.count_time(dt, self.time_limited):
                    self.q_direction = self.ran_direction.copy()
                    self.ran_direction.clear()
                    self.state = 'input'
        
        elif self.state == 'input':
            self.get_player_input()
            if len(self.input_direction) >= 4 :
                if not self.count_time(dt, 10):

                    if not self.check_correction:
                        self.chance -= 1
                        self.state = 'wrong'
                    else:
                        self.correct += 1
                        self.state = 'correct'    
        
        elif self.state == 'wrong':
            if not self.count_time(dt, 10):
                if self.chance >= 0:
                    self.input_direction.clear()
                    self.ran_direction.clear()
                    self.state = 'show'
                else:
                    self.state = 'over'
        
        elif self.state == 'correct':            
            if not self.count_time(dt, 10):
                if not self.win:
                    self.input_direction.clear()
                    self.ran_direction.clear()
                    self.state = 'show'
                else:
                    self.state = 'over'
        elif self.state == 'over':
            self.ani_timer += dt * 15
            if self.ani_timer >= 2:
                self.ani_timer = 0
                self.ani_idx += 1
            
            if self.ani_idx >= len(self.directon):
                self.ani_idx = 0
            
            sound_manager.play_sound("shadow.ogg")    
            
            if not self.count_time(dt, 15):
                scene_manager.change_scene(scene_manager.previous_screen_name)

    def count_time(self, dt, limited_time):
        if self.time_start <= limited_time:
            self.time_start += dt*self.speed
            return True
        else:
            self.time_start = 0
            return False
        
    def get_ran_direction(self):
        if self.ran_direction:
            return
        direction = random.choices(self.directon, k=4)
        self.ran_direction = direction

    def get_player_input(self):
        if len(self.input_direction)>=4:
            return
        
        if input_manager.key_pressed(pg.K_a):
            self.input_direction.append('left')
        elif input_manager.key_pressed(pg.K_d):
            self.input_direction.append('right')    
        elif input_manager.key_pressed(pg.K_w):
            self.input_direction.append('down')    
        elif input_manager.key_pressed(pg.K_s):
            self.input_direction.append('up')    
    
    def draw_ran_img(self, screen):
        if not self.ran_direction:
            return
        
        spacing = 150
        start_x = self.background.rect.centerx-50 - (spacing * 1.5)
        
        for i, direction in enumerate(self.ran_direction):
            surf = self.animation_surfs[direction]
            rect = surf.get_rect(center=(start_x + i * spacing, self.background.rect.centery+100))
            screen.blit(surf, rect)
    
    def draw_player_input(self, screen):
        if self.ran_direction or not self.input_direction:
            return
        
        spacing = 150
        start_x = self.background.rect.centerx-50 - (spacing * 1.5)
        
        for i, direction in enumerate(self.input_direction):
            surf = self.animation_surfs[direction]
            rect = surf.get_rect(center=(start_x + i * spacing, self.background.rect.centery+100))
            screen.blit(surf, rect)
    
    def text_output(self, screen, text):
        text_surf = self.extra_large.render(text, True, "black")
        text_rect = text_surf.get_rect(center=(self.title_rect.centerx, self.title_rect.y + self.title_rect.height*3))
        screen.blit(text_surf, text_rect)

    @property
    def check_correction(self):
        return all(self.input_direction[i] == self.q_direction[i] for i in range(len(self.input_direction))) 

    @property
    def win(self):
        return self.correct >=4
    
    def reset(self):
        self.state = "show"
        self.time_start = 0
        self.correct = 0
        self.chance = 3
        self.ran_direction.clear()
        self.q_direction.clear()
        self.input_direction.clear()


