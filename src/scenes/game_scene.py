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
from src.interface.components.chat_overlay import ChatOverlay

from typing import override, Dict, Tuple
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
        self.chat_overlay = None
        if GameSettings.IS_ONLINE:
            self.online_manager = OnlineManager()
            self.chat_overlay = ChatOverlay(
                send_callback=self.online_manager.send_chat,
                get_messages=self.online_manager.get_recent_chat 
            )
            self.game_manager.chat_overlay = self.chat_overlay
        else:
            self.online_manager = None
            
        self.online_player_animations: dict[int, Animation] = {}
        
        # Chat Bubbles
        self._chat_bubbles: Dict[int, Tuple[str, float]] = {}
        self._last_chat_id_seen = 0
        self._font = pg.font.Font(None, 24)

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
                
                # No Lerp (Instant snap like user requested)
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
                else:
                    anim.accumulator = 0  # Reset to first frame when stopped
                    
        # Update Chat Overlay
        if self.chat_overlay:
            # Only open on Enter. Do not close on Enter (Submit handles that, or ESC)
            if not self.chat_overlay.is_open and input_manager.key_pressed(pg.K_RETURN):
                self.chat_overlay.open()
            self.chat_overlay.update(dt)
            
        # Update Chat Bubbles
        if self.online_manager:
            try:
                msgs = self.online_manager.get_recent_chat(50)
                max_id = self._last_chat_id_seen
                now = time.monotonic()
                # Detect Server Reset (If we see IDs much lower than expected)
                if msgs and int(msgs[-1].get("id", 0)) < self._last_chat_id_seen:
                    self._last_chat_id_seen = 0

                for m in msgs:
                    mid = int(m.get("id", 0))
                    if mid <= self._last_chat_id_seen:
                        continue
                    sender = int(m.get("from", -1))
                    text = str(m.get("text", ""))
                    if sender >= 0 and text:
                        self._chat_bubbles[sender] = (text, now + 5.0)
                    if mid > max_id:
                        max_id = mid
                self._last_chat_id_seen = max_id
            except Exception:
                pass
        
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
        
        # Auto-save (Throttled to 5s)
        self._autosave_timer = getattr(self, '_autosave_timer', 0) + dt
        if self._autosave_timer > 5.0:
            self.auto_save.auto_save()
            self._autosave_timer = 0     
    
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
        
        # Bubbles
        if self.game_manager.player:
             self._draw_chat_bubbles(screen, self.game_manager.player.camera)
        
        self.minimap.navigation.draw_path(screen, camera)

        if not self.minimap.full_map:
            self.minimap.draw(screen)
        
        self.cycle.draw(screen)
        
        # full map
        if self.minimap.full_map:
            self.minimap.draw(screen)
            
        if self.chat_overlay:
            self.chat_overlay.draw(screen)
      
    def cycle_handle(self, dt):
        self.cycle.update(dt)
        self.cycle.draw_overlay = (self.game_manager.current_map_key == 'map.tmx')
        if self.game_manager.current_map_key == 'home.tmx':
            # from src.maps import Map
            
            obj_bed = self.game_manager.current_map.get_obj('bed')
            if obj_bed:
                rect = pg.rect.Rect(obj_bed.x, obj_bed.y, obj_bed.width, obj_bed.height)
                if self.game_manager.player.rect.colliderect(rect):
                    pass
        
        if scene_manager.next_scene_name == 'battle':
            self.cycle.get_pause_time()
        else:
            if scene_manager.next_scene_name == 'bag' and not scene_manager.previous_screen_name == 'battle':
                self.cycle.resume()
            if scene_manager.next_scene_name != 'bag':
                self.cycle.resume()

    def _draw_chat_bubbles(self, screen: pg.Surface, camera: PositionCamera) -> None:
        if not self.online_manager:
            return
            
        # REMOVE EXPIRED BUBBLES
        now = time.monotonic()
        expired = [pid for pid, (_, ts) in self._chat_bubbles.items() if ts <= now]
        for pid in expired:
             del self._chat_bubbles[pid]
        
        if not self._chat_bubbles:
            return

        # DRAW LOCAL PLAYER'S BUBBLE
        local_pid = self.online_manager.player_id
        if self.game_manager.player and local_pid in self._chat_bubbles:
            text, _ = self._chat_bubbles[local_pid]
            self._draw_chat_bubble_for_pos(screen, camera, self.game_manager.player.position, text, self._font)

        # DRAW OTHER PLAYERS' BUBBLES
        # Use animations for smoother position if available
        if not self.online_player_animations:
             return
             
        for pid, anim in self.online_player_animations.items():
            if pid not in self._chat_bubbles:
                continue
            
            # Use 'anim.position' which is the interpolated world pos
            # We assume if animation exists, they are on valid map (logic in update handles creation)
             
            text, _ = self._chat_bubbles[pid]
            self._draw_chat_bubble_for_pos(screen, camera, anim.position, text, self._font)

    def _draw_chat_bubble_for_pos(self, screen: pg.Surface, camera: PositionCamera, world_pos: Position, text: str, font: pg.font.Font):
        # for camera
        screen_pos = camera.transform_position_as_position(world_pos)
        
        # 2. Add screen center offset (player is rendered at screen center)
        sw, sh = screen.get_size()
        center_x = sw // 2
        center_y = sh // 2
        
        # Padding inside the bubble (around text)
        padding_x = 6
        padding_y = 4
        
        text_surf = font.render(text, True, (0, 0, 0))
        w = text_surf.get_width() + padding_x * 2
        h = text_surf.get_height() + padding_y * 2
            
        # scene blit padding
        bubble_x = center_x + screen_pos.x  # Right of player + 4px gap
        bubble_y = center_y + screen_pos.y - GameSettings.TILE_SIZE 
        
        # Draw Background
        rect = pg.Rect(bubble_x, bubble_y, w, h)
        pg.draw.rect(screen, (255, 255, 255), rect, border_radius=8)
        pg.draw.rect(screen, (0, 0, 0), rect, width=2, border_radius=8)
        
        # Draw Text
        screen.blit(text_surf, (bubble_x + padding_x, bubble_y + padding_y))