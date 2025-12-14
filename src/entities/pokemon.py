import pygame as pg
from src.utils import GameSettings
from src.sprites import BackgroundSprite
from src.scenes.scene import Scene
from src.interface.components import Button
from src.core.managers.pokemon_manager import PokemonManager
from src.core.services import scene_manager, sound_manager, input_manager, resource_manager

class Pokemon:
    def __init__(self, pokemon, hp, level,  b_pos: tuple, c_pos: tuple, flip:bool = False,  exp=None):
        self.pokemon_data = PokemonManager.get_pokemons()
        self.pokemon_img_path = PokemonManager.get_sprites()
        self.pokemon = pokemon #pokemon name
        
        self.small_font = resource_manager.get_font('Minecraft.ttf', 10)
        self.mid_font = resource_manager.get_font('Minecraft.ttf', 15)
        self.large_font = resource_manager.get_font('Minecraft.ttf', 20)

        #Banner setup
        self.banner = pg.transform.scale(resource_manager.get_image("UI/raw/UI_Flat_Banner04a.png"), (350, 85))
        self.banner_height = self.banner.get_height()
        self.banner_text = pg.Rect((0, GameSettings.SCREEN_HEIGHT-100), (GameSettings.SCREEN_WIDTH, 100))

        #hp
        self.hp = hp
        self.max_hp = self.pokemon_data[pokemon]['stats']['max_hp']
        
        #img
        self.flip = flip
        if self.flip:
            self.img_surf = pg.transform.scale(pg.transform.flip(resource_manager.get_image(self.pokemon_img_path[pokemon]), flip_x=True, flip_y=False), (80, 80))
        else:
            self.img_surf = pg.transform.scale(resource_manager.get_image(self.pokemon_img_path[pokemon]), (80, 80))
        
        self.name_surf = self.mid_font.render(pokemon, True, 'Black')
        
        #Level
        self.level = level
        self.lv_surf = self.large_font.render(F"Lv.{str(self.level)}", True, "#716A6A58")     
        self.exp_surf = self.mid_font.render(f"EXP:", True, "#FFFFFFB9")
        self.exp = exp
        self.max_exp = int(50 * (level ** 1.12))
        self.evolve = self.pokemon_data[pokemon].get('evolve', None)
        
        self.b_pos = b_pos  #banner pos   
        self.c_pos = c_pos  #center pos  
        
        self.animation = True
        self.catching = False
        self.animation_scale = 0
        self.rect = None
        self.surf = None

        #Store Atk and Dfs
        self.atk = self.pokemon_data[pokemon]['stats']['attack']
        self.dfs = self.pokemon_data[pokemon]['stats']['defense']
        
    def attack_animation(self):
        pass 
            
    def start_animation(self, screen):
        if self.animation:
            scale = int(250 * self.animation_scale)
            surf = pg.transform.scale(self.img_surf, (int(scale), int(scale)))
            rect = surf.get_rect(center = self.c_pos)
            screen.blit(surf, rect)

            self.animation_scale += 0.05
            if self.animation_scale >= 1:
                self.surf, self.rect = surf, rect
                self.animation = False
    
    def switch_animation(self):
        self.animation = True
        self.animation_scale = 0
        self.rect = None
        self.surf = None

    
    def catch_animation(self, screen):
        if not self.catching:
            return
        scale = int(self.rect.height / self.animation_scale)
        surf = pg.transform.scale(self.img_surf, (int(scale), int(scale)))
        rect = surf.get_rect(center = self.c_pos)
        screen.blit(surf, rect)

        self.animation_scale += 0.05
        if self.animation_scale >= 1:
            self.catching = False
    
    def evolve_pokemon(self):
        #change pokemon
        self.pokemon = self.evolve[0]
        
        # hp
        old_max_hp = self.max_hp
        self.max_hp = self.pokemon_data[self.pokemon]['stats']['max_hp']
        hp_boost = self.max_hp - old_max_hp
        self.hp = min(self.hp + hp_boost, self.max_hp)
        
        #img
        if self.flip:
            self.img_surf = pg.transform.scale(pg.transform.flip(resource_manager.get_image(self.pokemon_img_path[self.pokemon]), flip_x=True, flip_y=False), (80, 80))
        else:
            self.img_surf = pg.transform.scale(resource_manager.get_image(self.pokemon_img_path[self.pokemon]), (80, 80))
        
        self.name_surf = self.mid_font.render(self.pokemon, True, 'Black')

        #re-Store stat
        self.atk = self.pokemon_data[self.pokemon]['stats']['attack']
        self.dfs = self.pokemon_data[self.pokemon]['stats']['defense']
        self.max_exp = int(50 * (self.level ** 1.12))
        self.evolve = self.pokemon_data[self.pokemon].get('evolve', None)

        
        self.switch_animation()
        
    def add_level(self, amount):
        level_up = False
        evolved = False
        
        self.exp += amount
        while self.exp >= self.max_exp: # In case for update more than one
            self.exp -= self.max_exp
            self.level += 1
            self.max_exp = int(50 * (self.level ** 1.12))
            level_up = True
        self.lv_surf = self.large_font.render(F"Lv.{str(self.level)}", True, "#716A6A58")   

        if self.evolve and self.level >= self.evolve[1]:
            evolved = True
            self.evolve_pokemon()
            
        return level_up, evolved
    
    
    def draw_banner(self, screen):
        rect = self.banner.get_rect(topleft=self.b_pos)
        screen.blit(self.banner, rect)
        
        screen.blit(self.img_surf, (rect.x+20, rect.y-5)) #img
        screen.blit(self.name_surf, (rect.midleft[0]+100, rect.midleft[1]-20)) #name
        
        #Hp
        bar_width = (self.hp / self.max_hp)* 150
        pg.draw.rect(screen, "#5B6E56", (rect.midleft[0]+100, rect.midleft[1], 150, 15))
        pg.draw.rect(screen, '#D2DCB6', (rect.midleft[0]+100, rect.midleft[1], bar_width, 15))

        hp_text = self.small_font.render(f"{self.hp}/{self.max_hp}", True, "Black")
        screen.blit(hp_text, (rect.midleft[0]+100, rect.midleft[1]+20))
        screen.blit(self.lv_surf, (rect.midleft[0]+270, rect.midleft[1]))
        
        #exp
        if self.exp is not None:
            bar_width = (self.exp/self.max_exp) * 235
            pg.draw.rect(screen, "#262D24", (rect.x + 30, rect.bottom, 320, 20))  # BG
            pg.draw.rect(screen, "#777765", (rect.x + 80, rect.bottom+5, 235, 10))  # full bar
            pg.draw.rect(screen, "#769395", (rect.x + 80, rect.bottom+5, bar_width, 10))
            screen.blit(self.exp_surf, (rect.x + 40, rect.bottom+5))

    
    def draw(self, screen):
        self.draw_banner(screen)
        self.start_animation(screen)
        self.catch_animation(screen)

        if self.surf and self.rect:
            screen.blit(self.surf, self.rect)
