import pygame as pg

from src.utils import GameSettings
from src.sprites import BackgroundSprite
from src.scenes.scene import Scene
from src.interface.components import Button
from src.core.managers import GameManager
from src.core.services import scene_manager, sound_manager, input_manager, resource_manager
from src.entities.npc import NPC
from typing import override

class ShopScene(Scene):
    # Background Image
    background: BackgroundSprite

    game_manager: GameManager

    npc_shop : NPC
    
    def __init__(self):
        super().__init__()
        self.background = BackgroundSprite("UI/raw/UI_Flat_Frame03a.png", size=(GameSettings.SCREEN_WIDTH*2/3, GameSettings.SCREEN_HEIGHT*3/4), cpos=(GameSettings.SCREEN_WIDTH * 1 // 5, GameSettings.SCREEN_HEIGHT* 1// 7))
        self.game_manager = GameManager.get_instance()
        self.current_page = 0
        
        self.npc_shop = None
        self.pokemon_rect = []
        self.item_rect = []
        self.reset_count = 3
        self.day_reset = False

        self.selected_idx = None
        self.selected_type = None
        self.selected_surf = None
        self.selected_rect = None
        self.ui_setup()

        self.cycle = self.game_manager.day_night_cycle
        

    def ui_setup(self):
        #Button
        px, py = GameSettings.SCREEN_WIDTH // 2, GameSettings.SCREEN_HEIGHT* 3// 5
        self.button = {
            "reset": Button(
            "UI/raw/UI_Flat_Button01a_4.png", "UI/raw/UI_Flat_Button01a_3.png",
            self.background.rect.centerx+100, self.background.rect.centery-50, 70, 30,
            lambda: self.reset_stock(),
            text= "reset", size=15, color="#4A2828"
        ),
            "x": Button(
            "UI/button_x.png", "UI/button_x_hover.png",
            px+410, py-310, 35, 35,
            lambda: scene_manager.change_scene(scene_manager.previous_screen_name)
        )
        }
        self.next_button =Button(
            "UI/raw/UI_Flat_Button02a_2.png", "UI/raw/UI_Flat_Button02a_1.png",
            px+360, py+150, 40, 40,
            lambda: self.change_page(), 
            text= ">>", size=25, color="#EA0C0C"
        )
        self.back_button = Button(
            "UI/raw/UI_Flat_Button02a_2.png", "UI/raw/UI_Flat_Button02a_1.png",
            px+360, py+150, 40, 40,
            lambda: self.change_page(),
            text= "<<", size=25, color="#EA0C0C"
        )

        self.banner = pg.transform.scale(resource_manager.get_image("UI/raw/UI_Flat_Banner04a.png"), (350, 65))
        self.start_y = 100 # for banner
        self.banner_height = self.banner.get_height()

        #Buy overlay
        self.banner_overlay = pg.transform.scale(resource_manager.get_image("UI/raw/UI_Flat_FrameSlot03b.png"), (250, 50))
        self.confirm_button = None

        self.coins_font = resource_manager.get_font('Minecraft.ttf', 35)
        self.large_font = resource_manager.get_font('Minecraft.ttf', 30)
        self.mid_font = resource_manager.get_font('Minecraft.ttf', 20)
        self.small_font = resource_manager.get_font('Minecraft.ttf', 15)
        
        self.coins_surf = resource_manager.get_image('ingame_ui/coin.png', (30, 30))
        self.coins_rect = self.coins_surf.get_rect(topleft = (self.background.rect.centerx + 100, self.background.rect.centery-100))

    @override  
    def enter(self) -> None:
        self.npc_shop = self.game_manager.current_map.npc_shop
        self.shop_items = self.npc_shop.shop_items
        self.shop_pokemons = self.npc_shop.shop_pokemons
        self.reset_count = self.npc_shop.reset_count

        if self.npc_shop.are_sellout:
            self.shop_pokemons, self.shop_items = self.npc_shop.ran_stock()
        
        self.coins_count = self.game_manager.bag.items_data[0].get('count', 0)

        self.render_shop_pokemons()
        self.render_shop_item()
        

        self.previous_daystate = self.cycle.day_state
    
    @override
    def exit(self) -> None:
        self.npc_shop.shop_items = self.shop_items

        self.npc_shop.shop_pokemons = self.shop_pokemons
        self.npc_shop.reset_count = self.reset_count

        
    @override
    def update(self, dt: float) -> None:
        pass
        for button in self.button.values():
            button.update(dt)
        page_button = self.back_button if self.current_page == 1 else self.next_button
        page_button.update(dt)

        self.handle_hover_prices()
        self.render_buy_overlay()
        if self.confirm_button:
            self.confirm_button.update(dt)
        
        self.reset_per_day()


    
    @override
    def draw(self, screen: pg.Surface) -> None:
        if scene_manager.previous_screen_surf:
            screen.blit(scene_manager.previous_screen_surf, (0,0))
        overlay = pg.Surface((screen.get_size()), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        screen.blit(overlay, (0,0))
        
        self.background.draw(screen)
        for button in self.button.values():
            button.draw(screen)
        
        page_button = self.back_button if self.current_page == 1 else self.next_button
        page_button.draw(screen)

        screen.blit(self.coins_surf, self.coins_rect)
        self.draw_changable_text(screen)
        self.draw_list_pokemon(screen)
        self.draw_list_items(screen)

        if self.selected_idx is not None:
            screen.blit(self.banner_overlay, self.selected_rect)
            screen.blit(self.selected_surf, (self.selected_rect.x +15, self.selected_rect.y+15))
            self.confirm_button.draw(screen)
       
# --UI Part-- 
    def render_buy_overlay(self):
        if self.selected_idx is None:
            self.confirm_button = None
            return

        rect = None
        price = None
        if self.current_page == 0:
            selected = list(self.shop_pokemons.values())[self.selected_idx]
            rect = self.pokemon_rect[self.selected_idx]
            price = selected['price']
        
        elif self.current_page == 1:
            selected = list(self.shop_items.values())[self.selected_idx]
            rect = self.item_rect[self.selected_idx]
            price = selected['price']
        self.selected_surf = self.mid_font.render(f"Price: {price} coins", True, "#FFE8E8")
        self.selected_rect = self.banner_overlay.get_rect(topleft=(rect.x+rect.width-100, rect.y+rect.height/2))

        self.confirm_button = Button(
            "UI/button_shop.png", "UI/button_shop_hover.png",
            self.selected_rect.x +200, self.selected_rect.y+5, 40, 40,
            lambda: self.confirm_selected())

        
    
    def draw_changable_text(self, screen):
        #coins count
        count_surf = self.coins_font.render(f"Coins: {self.coins_count}", True, '#000000')
        count_rect = count_surf.get_rect(topleft = (self.coins_rect.right+20, self.coins_rect.top))
        screen.blit(count_surf, count_rect)

        #Reset count
        reset_surf = self.mid_font.render(f"Reset {self.reset_count}/3", True, '#000000')
        reset_rect = reset_surf.get_rect(topleft= (self.background.rect.centerx+190, self.background.rect.centery-40))
        screen.blit(reset_surf, reset_rect)
    
    def draw_list_pokemon(self, screen):
        if self.current_page == 1:
            return
        
        self.pokemon_rect = []
        for i, pokemon in self.shop_pokemons.items():
            idx = int(i)
            y_pos = self.start_y + (idx * self.banner_height)
            banner_rect = self.banner.get_rect(topleft=(300, y_pos+(idx*10)+50))
            self.pokemon_rect.append(banner_rect)
            self.draw_pokemon(screen, banner_rect, pokemon)

    def draw_pokemon(self, screen, banner_rect, pokemon):
        if pokemon['sold']:
            banner_copy = self.banner.copy()
            banner_copy.set_alpha(128)
            screen.blit(banner_copy, banner_rect)
            name_surf = pokemon['name_surf_sold']
            lv_surf = pokemon['lv_surf_sold']
            pic_surf = pokemon['pic_surf_sold']

        else:
            screen.blit(self.banner, banner_rect)
            name_surf = pokemon['name_surf']
            lv_surf = pokemon['lv_surf']
            pic_surf = pokemon['pic_surf']

        
        screen.blit(name_surf, (banner_rect.x + 100, banner_rect.y + 25))
        screen.blit(lv_surf, (banner_rect.x + 260, banner_rect.y + 30))
        screen.blit(pic_surf, (banner_rect.x + 20, banner_rect.y))

    def draw_list_items(self, screen):
        if self.current_page == 0:
            return
        
        self.item_rect = []
        for i, item in self.shop_items.items():
            idx = int(i)
            y_pos = self.start_y + (idx * self.banner_height*1.5)
            banner_rect = self.banner.get_rect(topleft=(300, y_pos+(idx*10)+50))
            self.item_rect.append(banner_rect)
            self.draw_shop_item(screen, banner_rect, item)

    def draw_shop_item(self,screen, banner_rect, item):
        if item['count'] < 0:
            banner_copy = self.banner.copy()
            banner_copy.set_alpha(128)
            screen.blit(banner_copy, banner_rect)
            name_surf = item['name_surf_sold']
            pic_surf = item['pic_surf_sold']

        else:
            screen.blit(self.banner, banner_rect)
            name_surf = item['name_surf']
            pic_surf = item['pic_surf']
        
        count_surf = self.small_font.render(f"Count: {item['count']}", True, "#000000")
        name_rect = name_surf.get_rect(center=(banner_rect.x + 170, banner_rect.y + 43))
        
        screen.blit(name_surf, name_rect)
        screen.blit(count_surf, (banner_rect.x + 250, banner_rect.y + 35))
        screen.blit(pic_surf, (banner_rect.x + 20, banner_rect.y))    
    
    def render_shop_pokemons(self):
        from src.core.managers import PokemonManager
        sprites = PokemonManager.get_sprites()
        for _, pokemon in self.shop_pokemons.items():
            sprite_path = sprites[pokemon['name']]
            pic = resource_manager.get_image(sprite_path)
            pic_surf = pg.transform.scale(pic, (60, 60))

            pokemon['name_surf'] = self.mid_font.render(pokemon['name'], True, '#000000')
            pokemon['name_surf_sold'] = self.mid_font.render(pokemon['name'], True, '#888888')
            pokemon['lv_surf'] = self.small_font.render(f"Lv.{pokemon['level']}", True, '#000000')
            pokemon['lv_surf_sold'] = self.small_font.render(f"Lv.{pokemon['level']}", True, '#888888')
            pokemon['pic_surf'] = pic_surf
            pic_surf_copy = pic_surf.copy()
            pic_surf_copy.set_alpha(128)
            pokemon['pic_surf_sold'] = pic_surf_copy
    
    def render_shop_item(self):
        for _, item in self.shop_items.items():
            pic = resource_manager.get_image(item['img_path'])
            pic_surf = pg.transform.scale(pic, (60, 60))
            
            item['name_surf'] = self.mid_font.render(item['name'], True, '#000000')
            item['name_surf_sold'] = self.mid_font.render(item['name'], True, '#888888')
            item['pic_surf'] = pic_surf
            pic_surf_copy = pic_surf.copy()
            pic_surf_copy.set_alpha(128)
            item['pic_surf_sold'] = pic_surf_copy
            
# --Logic part--
    def can_buy(self, item=None, pokemon=None):
        if item:
            return self.coins_count >= item['price'] and item['count'] > 0
        
        elif pokemon:
            return not pokemon['sold'] and self.coins_count >= pokemon['price']

        return False
    
    def handle_hover_prices(self):
        if self.current_page == 0:
            self.handle_pokemon_prices()
        else:
            self.handle_item_prices()

    def handle_item_prices(self):
        for i, rect in enumerate(self.item_rect):
            if rect.collidepoint(input_manager.mouse_pos):
                self.selected_idx = i
                self.selected_type = 'item'
                break
        else:
            if self.selected_rect and not self.selected_rect.collidepoint(input_manager.mouse_pos):
                self.selected_idx = None
                self.selected_type = None
        
    def handle_pokemon_prices(self):
        for i, rect in enumerate(self.pokemon_rect):
            if rect.collidepoint(input_manager.mouse_pos):
                selected = list(self.shop_pokemons.values())[i]
                if not selected['sold']:
                    self.selected_idx = i
                    self.selected_type = 'pokemon'
                else:
                    self.selected_idx = None
                    self.selected_type = None
                break
        else:
            if self.selected_rect and not self.selected_rect.collidepoint(input_manager.mouse_pos):
                self.selected_idx = None
                self.selected_type = None
    
    def confirm_selected(self):
        if self.selected_type is None:
            return
        from src.core.managers.autosave_manager import AutoSaveManager
        auto_save = AutoSaveManager(self.game_manager)
        
        if self.selected_type == 'pokemon':
            selected = list(self.shop_pokemons.values())[self.selected_idx]
            if self.can_buy(pokemon=selected):
                from src.core.managers.pokemon_manager import PokemonManager
                print(selected['name'])
                pokemon_data= PokemonManager.get_pokemons()
                pokemon = pokemon_data[selected['name']]
                self.game_manager.bag.monsters_data.append({
                    "name": selected['name'],
                    "hp": pokemon['stats']['max_hp'],
                    "max_hp": pokemon['stats']['max_hp'],
                    "level": selected['level'],
                    "exp": 0
                })
                self.game_manager.bag.items_data[0]['count'] -= selected['price']
                self.coins_count = self.game_manager.bag.items_data[0]['count']
                selected['sold'] = True
                self.render_shop_pokemons()


        elif self.selected_type == 'item':
            selected = list(self.shop_items.values())[self.selected_idx]
            if self.can_buy(item=selected):
                for item in self.game_manager.bag.items_data:
                    if item['name'].lower() == selected['name']:
                        item['count'] += 1
                        break
                else:
                    self.game_manager.bag.items_data.append({
                        "name": selected['name'],
                        "count": 1,
                        'sprite_path': selected['img_path']
                    })
                self.game_manager.bag.items_data[0]['count'] -= selected['price']
                self.coins_count = self.game_manager.bag.items_data[0]['count']
                selected['count'] -= 1

        
        auto_save.force_save()

    def reset_stock(self):
        if self.reset_count <= 0:
            return
        
        self.npc_shop.shop_items.clear()
        self.npc_shop.shop_pokemons.clear()
        self.shop_pokemons, self.shop_items = self.npc_shop.ran_stock()
        self.reset_count -= 1
        self.render_shop_item()
        self.render_shop_pokemons()

    def change_page(self):
        if self.current_page == 0:
            self.current_page += 1
            self.selected_idx = None
            self.selected_type = None
        else:
            self.current_page = 0
            self.selected_idx = None
            self.selected_type = None
    
    def reset_per_day(self):
        if 7 <=self.cycle.get_hours() <=12 and not self.day_reset:
            self.current_page = 0
            self.reset_count = 3
            self.day_reset = True

        else:
            self.day_reset = False 

