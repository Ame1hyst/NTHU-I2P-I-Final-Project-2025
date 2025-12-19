from __future__ import annotations
from src.utils import Logger, GameSettings, Position, Teleport
from src.core.managers import GameManager
import copy
import json, os
import pygame as pg
class AutoSaveManager:
    def __init__(self, game_manager:GameManager, path="saves/game0.json"):
        self.game_manager = game_manager
        self.path = path

        self.last_bag_data = None
        self.last_player_data = None
        self.last_map_key = None

        self.init_data()

    def init_data(self):
        # bag
        if self.game_manager.bag:
            self.last_bag_data = copy.deepcopy(self.game_manager.bag.to_dict())
        # player
        if self.game_manager.player:
            self.last_player_data = copy.deepcopy(self.game_manager.player.to_dict())
        # map
        self.last_map_key = self.game_manager.current_map_key

    @property
    def check_change(self):
        # bag
        if self.game_manager.bag:
            current = self.game_manager.bag
            if current != self.last_bag_data:
                return True        
        # player
        if self.game_manager.player:
            current = self.game_manager.player
            if current != self.last_player_data:
                return True        
        # map
        if self.last_map_key != self.game_manager.current_map_key:
            return True        
        return False
    
    def save(self):
        try:
            with open(self.path, "w") as f:
                json.dump(self.game_manager.to_dict(), f, indent=2)
            # Logger.info(f"Game auto-saved to {self.path}")
        except Exception as e:
            Logger.warning(f"Failed to auto-save game: {e}")
    
    def auto_save(self):
        if not self.check_change:
            return
        
        self.init_data()
        self.save()
    
    def force_save(self):
        self.init_data()
        self.save()