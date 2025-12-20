import pygame as pg
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.core.managers import GameManager

class DayNightCycle:
    def __init__(self, game_manager: "GameManager"):
        self.game_manager = game_manager
        
        self.start_time = pg.time.get_ticks()
        self.pause = False
        self.draw_overlay = True
        self.pause_time = 0
        self.day_length = 60 * 60 * 1000 # length cycle per day (15 min real)
        self.day_state = None
        self.time = self.game_manager.day_time
        self.overlay_color = None
    
    @property
    def time(self) -> float:
        return self.game_manager.day_time

    @time.setter
    def time(self, value: float):
        if value is None:
            self.game_manager.day_time = 0  #Defaut
        else:
            self.game_manager.day_time = value % 24
   
    @property
    def day_state(self) -> str:
        return self.game_manager.day_state

    @day_state.setter
    def day_state(self, value: str):
        self.game_manager.day_state = value
    
    def lerp(self, a, b, t): # For smooth change in overlay
        return a * (1 - t) + b * t
    
    def draw(self, screen):
        if not self.draw_overlay:
            return
        self.ui_screen(screen)

    def update(self, dt):        
        if not self.pause:
            hours_per_second = 24 / (self.day_length / 1000)
            self.time += dt * hours_per_second
            self.handle_day_state()
        else:
            self.time = None

    def get_time(self):
        return pg.time.get_ticks() - self.start_time

    def get_pause_time(self):
        self.pause_time = pg.time.get_ticks()
        self.pause = True
        

    def resume(self):
        if not self.pause:
            return
        pause = pg.time.get_ticks() - self.pause_time
        self.start_time += pause
        self.pause = False
        
    
    def get_hours(self): #Calculate base on day length
        return int(self.time)
    
    def get_minutes(self):
        return int((self.time % 1) * 60)
    
    def set_time(self, time):
        self.time = time

    def handle_day_state(self):
        if self.time is None:
            return
        
        current_time = self.time

        
        # DAWN Dark blue -> fading to soft pink/orange -> None overlay
        if 5.0 <= current_time < 7.0:
            self.day_state = 'dawn'
            progress = (current_time - 5.0) / 2.0  # 0.0 at 5:00, 1.0 at 7:00
            
            r = int(self.lerp(30, 227, progress))
            g = int(self.lerp(30, 136, progress))
            b = int(self.lerp(80, 62, progress))
            a = int(self.lerp(120, 0, progress))  # slow fade
            
            self.overlay_color = (r, g, b, a)
        
        elif 7.0 <= current_time < 17.0:
            self.day_state = 'day'
            self.overlay_color = (0, 0, 0, 0)  #full transparent
        
        # Evening Warm orange
        elif 17.0 <= current_time < 19.0:
            self.day_state = 'evening'
            progress = (current_time - 17.0) / 2.0  #0.0 at 17:00, 1.0 at 19:00
            
            r = int(self.lerp(255, 255, progress))
            g = int(self.lerp(220, 140, progress))
            b = int(self.lerp(180, 80, progress))
            a = int(self.lerp(0, 60, progress))  # slow appear
            
            self.overlay_color = (r, g, b, a)
        
        # DUSK Orange -> dark blue
        elif 19.0 <= current_time < 21.0:
            self.day_state = 'dusk'
            progress = (current_time - 19.0) / 2.0  # 0.0 at 19:00, 1.0 at 21:00
            
            r = int(self.lerp(255, 40, progress)) #255 176 142
            g = int(self.lerp(140, 40, progress))
            b = int(self.lerp(80, 100, progress))
            a = int(self.lerp(60, 130, progress))
            
            self.overlay_color = (r, g, b, a)
        
        # NIGHT Dark blue -> darkest
        else:
            self.day_state = 'night'
            
            if current_time >= 21.0:  # 21:00 to midnight
                progress = (current_time - 21.0) / 3.0  # 0.0 at 21:00, 1.0 at 0:00
                a = int(self.lerp(130, 160, progress))  # Getting darker
            else:  # midnight to 5:00
                progress = current_time / 5.0  # 0.0 at 0:00, 1.0 at 5:00
                a = int(self.lerp(160, 120, progress))  # Getting lighter
            
            # base dark blue color
            r, g, b = 40, 40, 100
            self.overlay_color = (r, g, b, a)
        
    def ui_screen(self, screen): #Do overlay trans
        if self.time is None:
            return
        overlay = pg.Surface(screen.get_size(), pg.SRCALPHA) # Base with alpha channel
        overlay.fill(self.overlay_color)
        screen.blit(overlay, (0, 0))
        

