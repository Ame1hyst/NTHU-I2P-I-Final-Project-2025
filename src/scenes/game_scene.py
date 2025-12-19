import pygame as pg
import threading
import time

from src.scenes.scene import Scene
from src.core import GameManager, OnlineManager, PokemonManager, AutoSaveManager
from src.utils import Logger, PositionCamera, GameSettings, Position
from src.interface.components import Button
from src.core.services import scene_manager, sound_manager, input_manager
from src.sprites import Sprite
from src.maps.minimap import MiniMap
from src.core.managers.achivevement_manager import AchieveManager
from src.sprites.animation import Animation


from typing import override
import sys



class GameScene(Scene):
    game_manager: GameManager
    online_manager: OnlineManager | None
    sprite_online: Sprite
    
    def __init__(self):
        super().__init__()
        #Online
        player_slot = int(sys.argv[1]) if len(sys.argv) > 1 else 0  # Get player slot from command line
        save_file = f"saves/game{player_slot}.json"
                
        # Load game manager
        manager = GameManager.load(
            save_file,  # Each player has their own save
        )

        # Game Manager
        GameManager.set_instance(manager) # Set game manager
        if manager is None:
            Logger.error("Failed to load game manager")
            exit(1)
        self.game_manager = GameManager.get_instance()
        self.auto_save = AutoSaveManager(self.game_manager)
        PokemonManager.get_instance()  

        self.cycle = self.game_manager.day_night_cycle
        self.minimap = MiniMap(scale=0.05)
        self.achievement_manager = AchieveManager()


        # Online Manager
        if GameSettings.IS_ONLINE:
            self.online_manager = OnlineManager()
        else:
            self.online_manager = None
        self.online_player_animations: dict[int, Animation] = {}

        #UI
        px, py = GameSettings.SCREEN_WIDTH, 0
        self.setting_button = Button(
            "UI/button_setting.png", "UI/button_setting_hover.png",
            px-80, py+25, 50, 50,
            lambda: scene_manager.change_scene("setting")
        )
        self.bag_button = Button(
            "UI/button_backpack.png", "UI/button_backpack_hover.png",
            px-140, py+25, 50, 50,
            lambda: self.open_bag()
        )
        self.achievement_button = Button(
            "krajua/button01.png", "krajua/hover_button01.png",
            px-200, py+25, 50, 50,
            lambda: scene_manager.change_scene("achievement")
        )
    # Set bag before change scene
    def open_bag(self):
        self.game_manager.current_bag = self.game_manager.bag
        scene_manager.change_scene("bag")   
        
    @override
    def enter(self) -> None:
        sound_manager.play_bgm("RBY 103 Pallet Town.ogg")
        self.cycle.resume()
        self.minimap.visible = True

        if self.online_manager:
            self.online_manager.enter()

            
    @override
    def exit(self) -> None:
        if self.online_manager:
            self.online_manager.exit()
        
        self.cycle.get_pause_time()
        self.minimap.visible = False
        
    @override
    def update(self, dt: float):
        # Check if there is assigned next scene
        self.game_manager.try_switch_map()
        
        # Update player and other data
        if self.game_manager.player:
            self.game_manager.player.update(dt)
        for enemy in self.game_manager.current_enemy_trainers:
            enemy.update(dt)
        
        # Update online players with interpolation
        if self.online_manager and self.game_manager.player:
            list_online = self.online_manager.get_list_players()
            
            for player in list_online:
                pid = player["id"]
                
                # Check map matching
                if player.get("map") != self.game_manager.current_map.path_name:
                    if pid in self.online_player_animations:
                        del self.online_player_animations[pid] # Cleanup
                    continue
                
                # Create animation if new player
                if pid not in self.online_player_animations:
                    self.online_player_animations[pid] = Animation(
                        "character/ow1.png",
                        ["down", "left", "right", "up"],
                        4,
                        (GameSettings.TILE_SIZE, GameSettings.TILE_SIZE)
                    )
                    # Initialize position ONLY when creating new animation
                    anim = self.online_player_animations[pid]
                    anim.position = Position(player["x"], player["y"])
                    anim.rect.topleft = (int(anim.position.x), int(anim.position.y))
                
                # Get animation (already exists)
                anim = self.online_player_animations[pid]
                direction = player.get("direction", "down")
                is_moving = player.get("is_moving", False)
                
                # Target position from server
                target_x = player["x"]
                target_y = player["y"]
                
                # Initialize position attribute if it doesn't exist
                if not hasattr(anim, 'position'):
                    anim.position = Position(target_x, target_y)
                
                # No Lerp (Instant snap test)
                anim.position = Position(target_x, target_y)

                
                # Update rect for rendering
                anim.rect.topleft = (int(anim.position.x), int(anim.position.y))
                
                # Switch direction
                if "none" in direction:
                    direction = "down"
                anim.switch(direction)
                
                # Animate if moving, freeze if stopped
                if is_moving:
                    anim.update(dt)
                    print(f"{pid} is moving {is_moving} in {direction}")
                else:
                    anim.accumulator = 0  # Reset to first frame when stopped
        
        # Update UI buttons
        self.setting_button.update(dt)
        self.bag_button.update(dt)
        self.achievement_button.update(dt)
        
        # Send local player update to server
        if self.game_manager.player is not None and self.online_manager is not None:
            movement_keys = [pg.K_LEFT, pg.K_RIGHT, pg.K_UP, pg.K_DOWN, 
                            pg.K_a, pg.K_d, pg.K_s, pg.K_w]
            is_moving = any(input_manager.key_down(key) for key in movement_keys)
            
            direction_str = str(self.game_manager.player.direction).lower()
            if "none" in direction_str:
                direction_str = "down"
            
            _ = self.online_manager.update(
                self.game_manager.player.position.x, 
                self.game_manager.player.position.y,
                self.game_manager.current_map.path_name,
                direction_str,
                is_moving
            )
        
        # Rest of updates
        self.achievement_manager.update_pham(self.game_manager.player)
        self.game_manager.current_map.update(dt, self.game_manager.player)
        self.minimap.update(dt)
        
        # Cycle handle
        self.cycle_handle(dt)
        
        # Auto-save
        self.auto_save.auto_save()     
    
    @override
    def draw(self, screen: pg.Surface):
        if self.game_manager.player:
            camera = PositionCamera(16 * GameSettings.TILE_SIZE, 30 * GameSettings.TILE_SIZE)
            camera = self.game_manager.player.camera
            self.game_manager.current_map.draw(screen, camera)
            self.achievement_manager.draw_pham(screen, camera)
            self.game_manager.player.draw(screen, camera)
        else:
            camera = PositionCamera(0, 0)
            self.game_manager.current_map.draw(screen, camera)
        for enemy in self.game_manager.current_enemy_trainers:
            enemy.draw(screen, camera)

        self.setting_button.draw(screen)
        self.bag_button.draw(screen)
        self.achievement_button.draw(screen)

        if self.online_manager and self.game_manager.player:
            list_online = self.online_manager.get_list_players()
            for player in list_online:
                if player["map"] == self.game_manager.current_map.path_name:
                    pid = player["id"]
                    if pid in self.online_player_animations:
                        anim = self.online_player_animations[pid]
                        is_moving = player.get("is_moving", False)
                        cam = self.game_manager.player.camera
                        anim.draw(screen, cam, key_press=is_moving)        
        
        self.minimap.navigation.draw_path(screen, camera)

        if not self.minimap.full_map:
            self.minimap.draw(screen)
        
        self.cycle.draw(screen)
        
        # full map
        if self.minimap.full_map:
            self.minimap.draw(screen)
      
    def cycle_handle(self, dt):
        self.cycle.update(dt)
        self.cycle.draw_overlay = (self.game_manager.current_map_key == 'map.tmx')
        if self.game_manager.current_map_key == 'home.tmx':
            # from src.maps import Map
            
            obj_bed = self.game_manager.current_map.get_obj('bed')
            rect = pg.rect.Rect(obj_bed.x, obj_bed.y, obj_bed.width, obj_bed.height)
            if self.game_manager.player.rect.colliderect(rect):
                print('hi')
        
        if scene_manager.next_scene_name == 'battle':
            self.cycle.get_pause_time()
        else:
            if scene_manager.next_scene_name == 'bag' and not scene_manager.previous_screen_name == 'battle':
                self.cycle.resume()
            if scene_manager.next_scene_name != 'bag':
                self.cycle.resume()