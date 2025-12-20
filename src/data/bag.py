import pygame as pg
import json
from src.utils import GameSettings
from src.core import GameManager
from src.utils.definition import Monster, Item
from src.sprites import BackgroundSprite
from src.interface.components import Button
from src.core.services import scene_manager, input_manager, resource_manager, sound_manager

class Bag():
    _monsters_data: list[Monster]
    _items_data: list[Item]

    def __init__(self, monsters_data: list[Monster] | None = None, items_data: list[Item] | None = None):
        self._monsters_data = monsters_data if monsters_data else []
        self._items_data = items_data if items_data else []
        self.pokemon_index_map = []
        self.potion_index = None
        self.battle_logic = None

        self.mode = None
        self.ui_setup()

    def ui_setup(self):
        #Button asset setup
        px, py = GameSettings.SCREEN_WIDTH // 2, GameSettings.SCREEN_HEIGHT* 3// 5
        self.background = BackgroundSprite("krajua/banner01.png", size=(GameSettings.SCREEN_WIDTH*0.9, GameSettings.SCREEN_HEIGHT*0.85), cpos=(GameSettings.SCREEN_WIDTH *0.15, GameSettings.SCREEN_HEIGHT* 0.1))
        self.x_button = Button(
            "UI/button_x.png", "UI/button_x_hover.png",
            px+380, py-330, 35, 35,
            lambda: scene_manager.change_scene(scene_manager.previous_screen_name))
        self.next_button = Button(
            "UI/raw/UI_Flat_Button02a_2.png", "UI/raw/UI_Flat_Button02a_1.png",
            px+120, py+170, 40, 40,
            lambda: self.next_page(), 
            text= ">>", size=25, color="#EA0C0C")
        self.back_button = Button(
            "UI/raw/UI_Flat_Button02a_2.png", "UI/raw/UI_Flat_Button02a_1.png",
            px+50, py+170, 40, 40,
            lambda: self.back_page(),
            text= "<<", size=25, color="#EA0C0C")

        self.large_font = resource_manager.get_font('Minecraft.ttf', 20)
        self.mid_font = resource_manager.get_font('Minecraft.ttf', 15)
        self.small_font = resource_manager.get_font('Minecraft.ttf', 10)
        
        self.banner = pg.transform.scale(resource_manager.get_image("UI/raw/UI_Flat_Banner04a.png"), (350, 65))
        self.start_y = 100 # for banner
        self.banner_height = self.banner.get_height()
        
        #Pokemon asset setup
        self.render_pokemon_list = []        
        self.render_item_list = []
        self.pokemon_rect = []
        self.item_rect = []
        self.start = 0
        self.stop = 6
    
    def enter(self) -> None:
        sound_manager.play_sound('open-bag-sound.mp3')

        self.game_manager = GameManager.get_instance()
        if scene_manager.previous_screen_name == 'game':
            self.mode = 'game'
            self._monsters_data = self.game_manager.bag._monsters_data
            self._items_data = self.game_manager.bag._items_data
            self.pokemon_index_map = list(range(len(self._monsters_data)))
        else:
            team_idx = self.game_manager.player_team_idx
            self.mode = 'battle'
            self._monsters_data = [self.game_manager.bag._monsters_data[i] for i in range(len(self.game_manager.bag._monsters_data)) if i in team_idx]
            self._items_data = self.game_manager.bag._items_data
            self.pokemon_index_map = team_idx
        
        self.render_pokemon()
        self.render_item()
    
    def exit(self) -> None:
        sound_manager.play_sound('open-bag-sound.mp3')

        self.render_pokemon_list.clear() # prevent caching
        self.render_item_list.clear()
        self.start, self.stop = 0, 6
        
        self.game_manager.save(path="saves/game0.json")
            
    def update(self, dt: float):
        self.x_button.update(dt)
        if self.mode == 'game':
            self.next_button.update(dt)
            self.back_button.update(dt)
        else:
            battle_scene = scene_manager.previous_screen
            # Safety check: Ensure previous screen handles battle actions
            if not hasattr(battle_scene, 'action_handle'):
                return
                
            if battle_scene.action_handle.current_turn == 'enemy':
                return
            #Change pokemon
            pokemon_index = self.change_pokemon()
            if pokemon_index is not None:
                battle_scene = scene_manager.previous_screen
                battle_scene.action_handle.current_player = pokemon_index
                battle_scene.players[pokemon_index].switch_animation()
                
                # Switch turn to enemy after changing pokemon
                battle_scene.action_handle.previous_turn = 'player'
                battle_scene.action_handle.current_turn = 'waiting'
                battle_scene.action_handle.state = 'battle'
                                
                scene_manager.change_scene(scene_manager.previous_screen_name)
            #Item using
            self.battle_logic = scene_manager.previous_screen.battle_logic
            self.item_used()
    
    def draw(self, screen: pg.Surface):
        if scene_manager.previous_screen_name in ['game', 'battle']: #not to draw immedieatly
            
            screen.blit(scene_manager.previous_screen_surf, (0,0))
            overlay = pg.Surface((screen.get_size()), pg.SRCALPHA)
            overlay.fill((0, 0, 0, 128))
            screen.blit(overlay, (0,0))

            self.background.draw(screen)
            self.x_button.draw(screen)
            if self.mode == 'game':
                self.next_button.draw(screen)
                self.back_button.draw(screen)
            self.draw_pokemon_list(screen)
            self.draw_item_list(screen)
            self.heal_system(screen)
    
    def render_pokemon(self):
        from src.core.managers import PokemonManager
        sprites = PokemonManager.get_sprites()
        for data in self.monsters_data[self.start:self.stop]:
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
    
    def render_item(self):
        if self.start >= len(self.monsters_data):
            return         

        for data in self._items_data:
            pic = resource_manager.get_image(data['sprite_path'])
            pic_surf = pg.transform.scale(pic, (50, 50)) if not data['name'].lower() == 'coins' else pg.transform.scale(pic, (30, 30))
            name_surf = self.large_font.render(str(data['name']), True, 'Black') if not data['name'].lower() == 'coins' else self.mid_font.render(str(data['name']), True, 'Black')
            count_surf = self.mid_font.render(f"X{data['count']}", True, 'Black') if not data['name'].lower() == 'coins' else self.small_font.render(f"X{data['count']}", True, 'Black')

            
            item_data = {
                'name': data['name'].lower(),
                'name_surf': name_surf,
                'pic_surf': pic_surf,
                'count_surf': count_surf
            }
            self.render_item_list.append(item_data)
    

    def draw_pokemon_list(self, screen: pg.Surface):
        if not self.render_pokemon_list:
            return
        
        self.pokemon_rect.clear()
        
        for i, pokemon in enumerate(self.render_pokemon_list):
            y_pos = self.start_y + (i * self.banner_height)
            banner_rect = self.banner.get_rect(topleft=(300, y_pos+(i*10)+50))
            self.pokemon_rect.append(banner_rect)
            self.draw_pokemon(screen, banner_rect, pokemon)

    def draw_pokemon(self, screen, banner_rect, pokemon):
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


    def draw_item_list(self, screen):
        if not self.render_item_list:
            return
        
        self.item_rect.clear()
        height = self.render_item_list[0]['pic_surf'].get_height() + 25
        
        idx = 0
        for item in self.render_item_list:
            if item['name'] == 'coins':
                rect = pg.Rect(self.banner.get_width()-50, 600, item['pic_surf'].get_width(), item['pic_surf'].get_height())
                self.item_rect.append(rect)
                self.draw_item(screen, rect, item)
                continue
            else:
                y_pos = self.start_y + (idx * height) + 55
                img_w, img_h = item['pic_surf'].get_width(), item['pic_surf'].get_height() 
                total_width = img_w + 100 + 80 # img + name area + count
                total_height = max(img_h, 50)
                rect = pg.Rect(self.banner.get_width()*2.1, y_pos, total_width, total_height)
                idx += 1
                self.item_rect.append(rect)
                self.draw_item(screen, rect, item)
    
    def draw_item(self, screen, rect, item):
            #Pic
            screen.blit(item['pic_surf'], (rect.x, rect.y))
            #Name
            screen.blit(item['name_surf'], (rect.x+100, rect.y+15))
            #Count
            screen.blit(item['count_surf'], (rect.x+250, rect.y+15))

    def next_page(self):
        if self.stop >= len(self.monsters_data):
            return
        self.start = self.stop
        self.stop = min(self.stop + 6, len(self.monsters_data))
        self.reset()
        self.render_pokemon()
        self.render_item()

    def back_page(self):
        self.start = max(self.start - 6, 0)
        self.stop = self.start + 6
        self.reset()
        self.render_pokemon()
        self.render_item()
    
    def heal_system(self, screen):
        if input_manager.mouse_down(pg.BUTTON_LEFT):
            for i, rect in enumerate(self.item_rect):
                if rect.collidepoint(input_manager.mouse_pos) and self.items_data[i]['name'].lower() == "potion" and self.items_data[i]['count'] > 0:
                    self.potion_index = i #  "Potion" Now have only 1, in case if want more potion in the future may change
                    break
        
        if self.potion_index is not None:
            item = self.render_item_list[self.potion_index]
            item_rect = item['pic_surf'].get_rect(center=input_manager.mouse_pos) # img go with mouse
            screen.blit(item['pic_surf'], item_rect)
        
        if input_manager.mouse_released(pg.BUTTON_LEFT) and self.potion_index is not None:

            heal = False
            heal_index = None
            for i, rect in enumerate(self.pokemon_rect):
                if rect.collidepoint(input_manager.mouse_pos):
                    real_index = i + self.start # order in game_manager
                    if not self.monsters_data[real_index]['hp'] == self.monsters_data[real_index]['max_hp']:
                        self.monsters_data[real_index]['hp'] = min(self.monsters_data[real_index]['hp'] + 50, self.monsters_data[real_index]['max_hp'])
                        self.items_data[self.potion_index]['count'] -= 1
                        sound_manager.play_sound('battle/heal.wav')
                        heal =True
                        heal_index = self.pokemon_index_map[real_index] # sync with order in list
                        break
            
            # Sync with battle scene if active
            if scene_manager.previous_screen_name == 'battle':
                battle_scene = scene_manager.previous_screen
                if battle_scene and heal_index in battle_scene.players:
                    battle_scene.players[heal_index].hp = self.monsters_data[real_index]['hp']                    
            
            if heal:
                self.render_pokemon_list.clear()
                self.render_item_list.clear()
                self.render_pokemon() # Update bag
                self.render_item()
                    
            self.potion_index = None # Not always render img

    def change_pokemon(self):
        if not scene_manager.previous_screen_name == 'battle':
             return None
      
        if input_manager.mouse_pressed(pg.BUTTON_LEFT):
            for i, rect in enumerate(self.pokemon_rect):
                if rect.collidepoint(input_manager.mouse_pos):
                    real_index = i + self.start
                    return self.pokemon_index_map[real_index]
        return None

    def item_used(self):
        if not scene_manager.previous_screen_name == 'battle':
             return
        
        if self.battle_logic is None:
            self.battle_logic = scene_manager.previous_screen.battle_logic
        
        if input_manager.mouse_pressed(pg.BUTTON_LEFT):
            for i, rect in enumerate(self.item_rect):
                if rect.collidepoint(input_manager.mouse_pos):
                    print(f"Clicked rect {i}: {self.items_data[i]['name']}")          
        if input_manager.mouse_pressed(pg.BUTTON_LEFT):
            for i, rect in enumerate(self.item_rect):
                if rect.collidepoint(input_manager.mouse_pos) and self.items_data[i]['count'] > 0:
                    item_name = self.items_data[i]['name'].lower()
                    if item_name not in ["attack buff", "dfs decrease", "defense buff"]:
                        continue
                    battle_scene = scene_manager.previous_screen
                    sound_manager.play_sound(f"battle/{item_name}.wav")
                    
                    if  item_name == "attack buff":
                        player_id = battle_scene.action_handle.current_player
                        self.battle_logic.set_buff("attack buff", player_id)
                        self.items_data[i]['count'] -= 1
                        
                        pokemon_name =  battle_scene.players[player_id].pokemon
                        battle_scene.action_handle.dialog.add_sequence([f"Player's{pokemon_name}'s Attack increased"])
                    elif item_name == "defense buff":
                        player_id = battle_scene.action_handle.current_player
                        self.battle_logic.set_buff("defense buff", player_id)
                        self.items_data[i]['count'] -= 1
                        
                        pokemon_name =  battle_scene.players[player_id].pokemon
                        battle_scene.action_handle.dialog.add_sequence([f"Player's {pokemon_name}'s Defense increased"])
                    elif item_name == "dfs decrease":
                        enemy_id = battle_scene.action_handle.current_enemy
                        self.battle_logic.set_buff("dfs decrease", enemy_id)
                        self.items_data[i]['count'] -= 1
                        
                        pokemon_name =  battle_scene.enemies[enemy_id].pokemon
                        battle_scene.action_handle.dialog.add_sequence([f"Enemy's {pokemon_name}'s Defense decreased"])
                    
                    self.render_item_list.clear()
                    self.render_item()
                    
                    # Switch turn to enemy after using item
                    battle_scene.action_handle.previous_turn = 'player'
                    battle_scene.action_handle.current_turn = 'waiting'
                    battle_scene.action_handle.state = 'battle'
                    battle_scene.action_handle.dialog.queue_call_back = battle_scene.action_handle.switch_turn
                    
                    scene_manager.change_scene(scene_manager.previous_screen_name)
                    return  
    
    def heal_all(self):
        for pokemon in self.monsters_data:
            pokemon['hp'] =pokemon['max_hp']
    
    def reset(self):
        self.potion_index = None

        self.start_y = 100
        self.banner_height = self.banner.get_height()
        self.render_pokemon_list = []        
        self.render_item_list = []
        self.pokemon_rect = []
        self.item_rect = []

    
    @property
    def monsters_data(self) -> list[Monster]:
        return self._monsters_data

    @property
    def items_data(self) -> list[Item]:
        return self._items_data
            
    def to_dict(self) -> dict[str, object]:
        return {
            "monsters": list(self._monsters_data),
            "items": list(self._items_data)
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Bag":
        monsters = data.get("monsters") or []
        items = data.get("items") or []
        bag = cls(monsters, items)
        return bag