from src.core.managers import GameManager
from src.utils import load_tmx, Position, GameSettings, PositionCamera, Teleport
from src.core.services import  input_manager, resource_manager
from src.maps.navigation import Navigation
import pygame as pg
class MiniMap:
    game_manager: GameManager
    def __init__(self, scale):
        self.game_manager = GameManager.get_instance()
        self.mini_v = (200, 150)
        self.full_v = (600, 450)
        self.v_scale = self.mini_v

        self.scale = scale
        self.padding = 10
        self.screen_pos = (self.padding, self.padding)
        
        self.visible = True
        self.full_map = False

        self.current_map = None   
        self._cached_map_key = None
        self._base_surface = None

        # #Navigation setup
        self.navigation = Navigation(self.game_manager)

        #time font
        self.small_font = resource_manager.get_font('Minecraft.ttf', 20)
        self.large_font = resource_manager.get_font('Minecraft.ttf', 30)
    
    def draw(self, screen: pg.Surface):
        if not self.visible:
            return
        
        if self._base_surface is None:
            self.resize_map()

        
        mini_surf = self._base_surface.copy()
        self.draw_npc(mini_surf)
        self.draw_statue(mini_surf)
        self.draw_trainer(mini_surf)
        self.draw_player(mini_surf)

        screen.blit(mini_surf, self.screen_pos)      
        # Border
        pg.draw.rect(screen, "#000000", (*self.screen_pos, self.mini_w, self.mini_h), 2)


        if self.full_map:
            self.navigation.draw(screen, self.screen_pos, self.v_scale)
        
        self.draw_time(screen)
    
    def update(self, dt):
        self.re_build_mini_map()
        self.handle_state()

        self.navigation.update(dt)



    def resize_map(self):
        self.current_map = self.game_manager.current_map
        tmx = self.current_map.tmxdata
        
        self.map_width = tmx.width * GameSettings.TILE_SIZE
        self.map_height = tmx.height * GameSettings.TILE_SIZE
            
                
        # cal scale to fit in minimap
        scale_x = self.v_scale[0] / self.map_width
        scale_y = self.v_scale[1] / self.map_height
        self.scale = min(scale_x, scale_y) 

        # mini map size
        self.mini_w, self.mini_h = self.v_scale

        # Tile size on minimap (at least 1 pixel)
        self.tile_px = max(1, int(GameSettings.TILE_SIZE * self.scale))

        #Resize 
        self._base_surface = pg.transform.smoothscale(self.current_map._surface, (self.mini_w, self.mini_h))
        
        self._cached_map_key = self.game_manager.current_map_key # prevent cach
   
    def re_build_mini_map(self):
        if self._cached_map_key != self.game_manager.current_map_key:
            self.resize_map()
            self.navigation.reset()
            self.navigation.render_ui(self.screen_pos, self.v_scale)    
    
    def get_mini_pos(self, pos:tuple):
        scale_x = self.v_scale[0] / self.map_width
        scale_y = self.v_scale[1] / self.map_height
        scale = min(scale_x, scale_y)

        offset_x = (self.v_scale[0] - self.map_width * scale) / 2
        offset_y = (self.v_scale[1] - self.map_height * scale) / 2

        x = int(pos[0] * scale + offset_x)
        y = int(pos[1] * scale + offset_y)
        return (x, y)    
    
    def draw_trainer(self, screen):
        if not self.game_manager.current_enemy_trainers:
            return
        
        for trainer in self.game_manager.current_enemy_trainers:
            pos = (trainer.position.x, trainer.position.y)
            mini_pos = self.get_mini_pos(pos)
            pg.draw.circle(screen, "red", mini_pos, 3)
    
    def draw_player(self, screen):
        if not self.game_manager.player:
            return
        pos = (self.game_manager.player.x, self.game_manager.player.y)
        mini_pos = self.get_mini_pos(pos)
        pg.draw.circle(screen, "white", mini_pos, 5)  # border
        pg.draw.circle(screen, "black", mini_pos, 3)   # fill
    
    def draw_npc(self, surf):
        if not self.current_map.npc_shop:
            return
        
        pos = self.current_map.npc_shop.position.x, self.current_map.npc_shop.position.y
        mini_pos = self.get_mini_pos(pos)
        pg.draw.rect(surf, "White", (*mini_pos, self.tile_px, self.tile_px))
    
    def draw_statue(self, surf):
        if not self.current_map.healing_statue:
            return
        statue = self.current_map.healing_statue
        pos = (statue.statue_rect.x, statue.statue_rect.y)
        mini_pos = self.get_mini_pos(pos)
        pg.draw.rect(surf, "blue", (*mini_pos, self.tile_px, self.tile_px))

    def draw_time(self, screen):
        cycle = self.game_manager.day_night_cycle
        hours = cycle.get_hours()
        minutes = cycle.get_minutes()
        state = cycle.day_state.capitalize() if cycle.day_state else "Unknown"
        
        font = self.small_font if not self.full_map else self.large_font
        
        time_str = f"{state} - {hours:02d}:{minutes:02d}"
        time_surf = font.render(time_str, True, "white")
        
        pos_x = self.screen_pos[0] + 5
        pos_y = self.screen_pos[1] + self.mini_h + 10
        

        shadow_surf = font.render(time_str, True, "black")               
        screen.blit(shadow_surf, (pos_x + 1, pos_y + 1))
        screen.blit(time_surf, (pos_x, pos_y))

    
    def handle_state(self):
        if not (self._base_surface and self.screen_pos):
            return
        
        rect = pg.Rect((self.screen_pos), (self.v_scale)) #get the actual pos
        if input_manager.mouse_pressed(pg.BUTTON_LEFT):
            if rect.collidepoint(input_manager.mouse_pos) and not self.full_map:
                self.handle_map_size()
            elif not rect.collidepoint(input_manager.mouse_pos) and self.full_map:
                self.handle_map_size()
            

    def handle_map_size(self):
        self.full_map = not self.full_map
        if self.full_map:  
            self.v_scale = self.full_v
            self.screen_pos = ((GameSettings.SCREEN_WIDTH - self.v_scale[0] -150) // 2, (GameSettings.SCREEN_HEIGHT - self.v_scale[1]) // 2)
            self.navigation = Navigation(self.game_manager)
            self.navigation.render_ui(self.screen_pos, self.v_scale)            
        else:
            self.v_scale = self.mini_v
            self.screen_pos = (self.padding,self.padding)
        
        self._base_surface = None
        self.resize_map()
    




