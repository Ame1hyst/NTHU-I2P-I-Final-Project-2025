import pygame as pg

from src.utils import load_tmx, Position, GameSettings, PositionCamera, Teleport
from src.sprites import BackgroundSprite
from src.scenes.scene import Scene
from src.interface.components import Button
from src.core.managers import GameManager
from src.core.services import scene_manager, sound_manager, input_manager, resource_manager
from typing import override
import json
from src.interface.components.dialog import Dialog
from src.additional.pham import Pham

class AchieveManager:
    def __init__(self):
        self.game_manager = GameManager.get_instance()
        self.current_map = None
        self.achievement_data = self.load()
        
        self.pham_data:list[Pham] = []
        self.warning = False
        self.current_pham = None

        self.render_pham()
        
        #warning Animation
        self.waring_surf = resource_manager.get_image('krajua/warning.png', (50, 50))

    
    def load(self):
        with open('saves/achievement_data.json', "r") as f:
            return json.load(f)
    @property
    def progress(self):
        return self.game_manager.achievement
    
    
    def check_unlocked(self, trigger):
        if not self.progress.get("unlocked", []):
            self.progress['unlocked'] = self.progress.get("unlocked", [])
        
        if trigger in self.progress['unlocked']:
            return False
    
        if trigger == "pham_collected":
            required = self.achievement_data.get("required_count", 5)
            return len(self.progress.get("pham_collected", [])) >= required
        elif trigger == "heal_count":
            required = self.achievement_data.get("required_count", 10)
            return self.progress.get("heal_count", 0) >= required
        elif trigger == "pokemon_caught":
            total_pokemon = 16
            return len(self.progress.get("pokemon_caught", [])) >= total_pokemon
        elif trigger == "boss_defeated":
            return self.progress.get("boss_defeated", False)
        elif trigger == "all_achievements" and len(self.progress['unlocked']) >= 4:
            return self.all_unlocked()
        
        return False

    # --Collected Pham--   
    def draw_pham(self, screen, camera:PositionCamera):
        if not self.pham_data:
            return
        
        for pham in self.pham_data:
            pham.draw(screen, camera)
            if GameSettings.DRAW_HITBOXES:
                pg.draw.rect(screen, (255, 0, 0), camera.transform_rect(pham.rect), 1)
        if self.warning and self.current_pham:
            screen.blit(self.waring_surf, camera.transform_rect(self.current_pham.rect).topleft)    

    def update_pham(self, player):
        if self.game_manager.current_map != self.current_map:
            self.render_pham()
        
        if not self.pham_data:
            return
        
        for pham in self.pham_data:
            if self.check_pham_collision(pham.rect, player.rect):
                self.warning = True
                self.current_pham = pham
                break
        else:
            self.warning = False
        
        if self.warning and input_manager.key_down(pg.K_SPACE) and not self.is_pham_collected(self.current_pham.id):
            self.collect_pham(self.current_pham.id)
            self.pham_data.remove(self.current_pham)  #remove
            self.warning = False
            self.current_pham = None
        
    def is_pham_collected(self, pham_id: str) -> bool:
        return pham_id in self.progress.get("pham_collected", [])
    
    def collect_pham(self, pham_id: str):
        if not self.progress.get("pham_collected", []):
            self.progress["pham_collected"] = self.progress.get("pham_collected", [])
        
        if pham_id not in self.progress["pham_collected"]:
                self.progress["pham_collected"].append(pham_id)
                if self.check_unlocked("pham_collected"):
                    self.progress["unlocked"].append('pham_collected')
                    self.check_all_achievements()
   
    def check_pham_collision(self, rect:pg.Rect, player_rect):
        if not self.game_manager:
            return False
        self.current_map = self.game_manager.current_map
        if not self.game_manager.current_map.pham_located:
            return False
        
        if rect.colliderect(player_rect):
            return True
        
        return False
    
    def render_pham(self):
        self.reset_pham()
        
        if self.game_manager.current_map == self.current_map:
            return    
        
        self.current_map = self.game_manager.current_map
        pham_data = self.current_map.pham_located
        
        for pham in pham_data:
            if pham['id'] not in self.progress.get("pham_collected", []):
                self.pham_data.append(Pham.from_dict(pham))
    
    def reset_pham(self):
        self.pham_data.clear()
        self.warning = False
        self.current_pham = None

    # -- Collected Pokemon--
    def add_caught_pokemon(self, pokemon_name):
        if not self.progress.get("pokemon_caught", []):
            self.progress["pokemon_caught"] = []
        
        if pokemon_name not in self.progress["pokemon_caught"]:
            self.progress["pokemon_caught"].append(pokemon_name)
            if self.check_unlocked("pokemon_caught"):
                self.progress["unlocked"].append('pokemon_caught')
                self.check_all_achievements()
    
    # --Healing count--
    def add_heal_count(self):
        self.progress["heal_count"] = self.progress.get("heal_count", 0) + 1
        if self.check_unlocked("heal_count"):
            self.progress["unlocked"].append('heal_count')
            self.check_all_achievements()
    
    #--FIght Boss--
    def defeated_boss(self):
        if not self.game_manager.current_map_key == 'gym.tmx':
            return
        
        self.progress["boss_defeated"] = True
        if self.check_unlocked("boss_defeated"):
            self.progress["unlocked"].append('boss_defeated')
            self.check_all_achievements()

    #--Check all achievements--
    def all_unlocked(self):
        required_achievements = ["pham_collected", "pokemon_caught", "heal_count", "boss_defeated"]
        unlocked = self.progress.get("unlocked", [])
        return all(ach in unlocked for ach in required_achievements)

    def check_all_achievements(self):
        """Check if all 4 main achievements are unlocked, then unlock the final achievement"""
        if self.all_unlocked() and "all_achievements" not in self.progress.get("unlocked", []):
            self.progress["unlocked"].append("all_achievements")
