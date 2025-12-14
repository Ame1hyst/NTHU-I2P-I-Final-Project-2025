import pygame as pg
from src.utils import GameSettings
from src.scenes.scene import Scene
from src.sprites import BackgroundSprite
from src.interface.components import Button
from src.core.managers import GameManager, PokemonManager, AutoSaveManager
from src.core.services import scene_manager, sound_manager, input_manager, resource_manager
from typing import override
import random

class SelectedPokemon(Scene):
    def __init__(self):
        super().__init__()
        self.game_manager = None
        self.selected_pokemons = []
        self.selection_buttons = {}
        self.max_select = 6
        self.selected_num = 0
        self.ui_setup()    
    
    def ui_setup(self):
        #Button asset setup
        px, py = GameSettings.SCREEN_WIDTH // 2, GameSettings.SCREEN_HEIGHT* 3// 5
        self.background = BackgroundSprite("krajua/banner03.png", size=(GameSettings.SCREEN_WIDTH*0.9, GameSettings.SCREEN_HEIGHT*0.85), cpos=(GameSettings.SCREEN_WIDTH  *0.15, GameSettings.SCREEN_HEIGHT* 0.1))
        self.x_button = Button(
            "UI/button_x.png", "UI/button_x_hover.png",
            px+470, py-320, 35, 35,
            lambda: scene_manager.change_scene(scene_manager.previous_screen_name))
        self.next_button = Button(
            "UI/raw/UI_Flat_Button02a_2.png", "UI/raw/UI_Flat_Button02a_1.png",
            px+470, py+170, 40, 40,
            lambda: self.next_page(), 
            text= ">>", size=25, color="#EA0C0C")
        self.back_button = Button(
            "UI/raw/UI_Flat_Button02a_2.png", "UI/raw/UI_Flat_Button02a_1.png",
            px+120, py+170, 40, 40,
            lambda: self.back_page(),
            text= "<<", size=25, color="#EA0C0C")
        self.battle_button = Button(
            "UI/raw/UI_Flat_FrameSlot01b.png", "UI/raw/UI_Flat_FrameSlot01c.png",
            self.background.rect.centerx+80, self.background.rect.centery, 200, 50, 
            lambda: self.handle_enter_battle(), text="Battle", size=20)
        
        
        self.extra_large = resource_manager.get_font('Minecraft.ttf', 40)
        self.large_font = resource_manager.get_font('Minecraft.ttf', 20)
        self.mid_font = resource_manager.get_font('Minecraft.ttf', 15)
        self.small_font = resource_manager.get_font('Minecraft.ttf', 10)
        
        self.banner = pg.transform.scale(resource_manager.get_image("UI/raw/UI_Flat_Banner04a.png"), (350, 65))
        self.start_y = 100 # for banner
        self.banner_height = self.banner.get_height()
        
        #Pokemon asset setup
        self.render_pokemon_list = []        
        self.pokemon_rect = []
        self.item_rect = []
        self.start = 0
        self.stop = 6

    @override
    def enter(self):
        self.game_manager = GameManager.get_instance()
        self.render_button()
        self.render_pokemon()

    @override
    def update(self, dt):
        # Update only visible button
        for i in range(self.start, min(self.stop, len(self.selection_buttons))):
            if i in self.selection_buttons:
                self.selection_buttons[i].update(dt)  
        
        self.x_button.update(dt)
        self.next_button.update(dt)
        self.back_button.update(dt)
        self.battle_button.update(dt)



    @override
    def draw(self, screen):
        screen.blit(scene_manager.previous_screen_surf, (0,0))
        overlay = pg.Surface((screen.get_size()), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        screen.blit(overlay, (0,0))

        self.background.draw(screen)
        self.x_button.draw(screen)
        self.next_button.draw(screen)
        self.back_button.draw(screen)
        self.battle_button.draw(screen)
        self.draw_pokemon_list(screen)
        
        #Text title setup
        max_text_surf = self.extra_large.render(f"Selected: {self.selected_num }/{self.max_select}", True, "#414141")
        screen.blit(max_text_surf, (self.background.rect.centerx+50, self.background.rect.centery-100))

    @override
    def exit(self):
        self.reset()
        self.selected_pokemons = []
        self.selection_buttons = {}
        self.max_select = 6
        self.selected_num = 0

        self.start = 0
        self.stop = 6


    
    def render_button(self):
        for i in range(len(self.game_manager.bag.monsters_data)):
            button = Button(
                "UI/raw/UI_Flat_ToggleLeftOff01a.png",
                "UI/raw/UI_Flat_ToggleLefton01a.png",
                0, 0, 50, 30,  # Position updated in draw_pokemon()
                lambda idx=i: self.handle_selected_pokemon(idx)
            )
            self.selection_buttons[i] = button

    def render_pokemon(self):
        self.render_pokemon_list.clear()
        sprites = PokemonManager.get_sprites()
        for data in self.game_manager.bag.monsters_data[self.start:self.stop]:
            sprite_path = sprites[data['name']]
            pic = resource_manager.get_image(sprite_path)
            pic_surf = pg.transform.scale(pic, (60, 60))
            name_surf = self.mid_font.render(str(data['name']), True, 'Black')
            hp_surf = self.small_font.render(f"{ data['hp']}/{data['max_hp']}", True, 'Black')
            lv_surf = self.large_font.render(f"Lv.{data['level']}", True, 'Black')

                    
            pokemon_data = {
                'name_surf': name_surf,
                'pic_surf': pic_surf,
                'hp': data['hp'],
                'max_hp': data['max_hp'],
                'hp_surf': hp_surf,
                'lv_surf': lv_surf
                    }
            self.render_pokemon_list.append(pokemon_data)    
    
    def draw_pokemon_list(self, screen: pg.Surface):
        if not self.render_pokemon_list:
            return
        
        self.pokemon_rect.clear()
        
        for i, pokemon in enumerate(self.render_pokemon_list):
            y_pos = self.start_y + (i * self.banner_height)
            banner_rect = self.banner.get_rect(topleft=(300, y_pos+(i*10)+50))
            self.pokemon_rect.append(banner_rect)
            self.draw_pokemon(screen, banner_rect, pokemon, i)

    def draw_pokemon(self, screen, banner_rect, pokemon, index):
            #Banner
            screen.blit(self.banner, banner_rect)
            #Name
            screen.blit(pokemon['name_surf'], (banner_rect.x + 100, banner_rect.y + 15))
            #Pic
            screen.blit(pokemon['pic_surf'], (banner_rect.x+20, banner_rect.y))
            #Hp
            bar_width = (pokemon['hp'] / pokemon['max_hp']) * 150
            pg.draw.rect(screen, '#778873', (banner_rect.midleft[0]+100, banner_rect.midleft[1], 150, 15)) #Bg bar
            pg.draw.rect(screen, '#D2DCB6', (banner_rect.midleft[0]+100, banner_rect.midleft[1], bar_width, 15)) #Hp bar
            
            screen.blit(pokemon['hp_surf'], (banner_rect.x+100, banner_rect.y+50))
            #Level
            screen.blit(pokemon['lv_surf'], (banner_rect.x+260, banner_rect.y+30))

            #Selected check list
            real_index = index + self.start
            select_button = self.selection_buttons[real_index]
        
            select_button.hitbox.x = banner_rect.topright[0]
            select_button.hitbox.y = banner_rect.topright[1]
        
            select_button.is_clicked = real_index in self.selected_pokemons
            
            select_button.draw(screen)
    
    def handle_selected_pokemon(self, index):
        button = self.selection_buttons[index]
        if index in self.selected_pokemons:
            self.selected_num -= 1
            button.is_clicked = False
            self.selected_pokemons.remove(index)
        elif len(self.selected_pokemons) < self.max_select:
            self.selected_num += 1
            button.is_clicked = True
            self.selected_pokemons.append(index)
    
    def next_page(self):
        if self.stop >= len(self.game_manager.bag.monsters_data):
            return
        self.start = self.stop
        self.stop = min(self.stop + 6, len(self.game_manager.bag.monsters_data))
        self.reset()
        self.render_pokemon()


    def back_page(self):
        self.start = max(self.start - 6, 0)
        self.stop = self.start + 6
        self.reset()
        self.render_pokemon()

    def reset(self):
        #Pokemon asset setup
        self.render_pokemon_list = []        
        self.pokemon_rect = []
        self.item_rect = []

    def handle_enter_battle(self):
        if self.selected_num > 6 or not self.selected_num:
            return
        self.game_manager.player_team_idx = sorted(self.selected_pokemons)
        scene_manager.change_scene('battle')

