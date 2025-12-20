from __future__ import annotations
from src.utils import Logger, GameSettings, Position, Teleport
from src.additional.day_night_cycle import DayNightCycle
import json, os
import pygame as pg
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.maps.map import Map
    from src.entities.player import Player
    from src.entities.enemy_trainer import EnemyTrainer
    from src.data.bag import Bag
    

class GameManager:
    _instance = None
    # Entities
    player: Player | None
    enemy_trainers: dict[str, list[EnemyTrainer]]
    bag: "Bag"

    # Map properties
    current_map_key: str
    maps: dict[str, Map]
    
    # Changing Scene properties
    should_change_scene: bool
    next_map: str
    next_teleport: Teleport
    
    def __init__(self, maps: dict[str, Map], start_map: str, 
                player: Player | None,
                player_spwans: dict[str, Position],
                enemy_trainers: dict[str, list[EnemyTrainer]], 
                bag: Bag | None = None,
                healing_statue = {},
                achievement = {},
                day_time:float = None,
                save_path: str = "saves/game0.json"):  # ADD THIS
                    
        from src.data.bag import Bag
        # Game Properties
        self.maps = maps
        self.current_map_key = start_map
        self.player = player
        self.player_spawns = player_spwans
        self.enemy_trainers = enemy_trainers
        self.bag = bag if bag is not None else Bag([], [])
        self.save_path = "saves/game0.json"
       
        #Additional
        self.healing_statue = healing_statue or {} #healing
        self.achievement = achievement # Achievement
        
        self.day_time = day_time
        self.day_state = "day"
        self.day_night_cycle = DayNightCycle(self)


        #Battle team
        self.player_team_idx = []
        
        # Check If you should change scene
        self.should_change_scene = False
        self.next_map = ""
        self.next_teleport = None 
        
    @property
    def current_map(self) -> Map:
        return self.maps[self.current_map_key]
        
    @property
    def current_enemy_trainers(self) -> list[EnemyTrainer]:
        return self.enemy_trainers.get(self.current_map_key, [])
        
    @property
    def current_teleporter(self) -> list[Teleport]:
        return self.maps[self.current_map_key].teleporters
        
    def get_map_scale(self, map_name: str) -> int:
        if map_name in ['home.tmx', 'shop.tmx']:
            return 2
        return 1

    def scale_entities(self):
        scale = self.get_map_scale(self.current_map_key)
        
        if self.player:
            self.player.set_scale(scale)
        
        if self.current_enemy_trainers:
            for trainer in self.current_enemy_trainers:
                trainer.set_scale(scale)  
        if self.current_map.npc_shop:
            self.current_map.npc_shop.set_scale(scale)

    def get_tile_size(self): # for scale change
        return GameSettings.TILE_SIZE * self.get_map_scale(self.current_map_key)
    
    def switch_map(self, tp: Teleport) -> None:
        if tp.destination not in self.maps:
            Logger.warning(f"Map '{tp.destination}' not loaded; cannot switch.")
            return
        
        self.next_map = tp.destination
        self.should_change_scene = True
        self.next_teleport = tp
            
    def try_switch_map(self) -> None:
        if self.should_change_scene:
            self.current_map_key = self.next_map
            self.next_map = ""
            self.should_change_scene = False
            if self.player:
                self.player.position = self.next_teleport.dest_pos # go to dest pos
                #Collision Update
                self.player.x = self.player.position.x
                self.player.y = self.player.position.y
                
                self.scale_entities()           
            
            self.next_teleport = None
            
    def check_collision(self, rect: pg.Rect) -> bool:
        if self.maps[self.current_map_key].check_collision(rect):
            return True
        if self.current_enemy_trainers:
            for entity in self.enemy_trainers[self.current_map_key]:
                if rect.colliderect(entity.animation.rect):
                    return True
        if self.current_map.npc_shop:
            entity = self.current_map.npc_shop
            if rect.colliderect(entity.animation.rect):
                return True
            
        
        return False
    
    def check_bush(self, rect: pg.Rect) -> bool:
        if self.maps[self.current_map_key].check_bush(rect):
            return True
        return False

        
    def save(self, path: str) -> None:
        save_path = path or self.save_path
        try:
            with open(save_path, "w") as f:
                json.dump(self.to_dict(), f, indent=2)
            Logger.info(f"Game saved to {save_path}")
        except Exception as e:
            Logger.warning(f"Failed to save game: {e}")             
    @classmethod
    def load(cls, path: str) -> "GameManager | None":
        # Create from template if doesn't exist
        if not os.path.exists(path):
            template = "saves/backup.json"
            if os.path.exists(template):
                Logger.info(f"Creating new save file from template: {path}")
                import shutil
                shutil.copy(template, path)
            else:
                # Fallback to game0.json only if we are NOT trying to load game0.json
                # But really, backup.json should exist.
                Logger.error(f"No template found: {template}")
                return None

        try:
            with open(path, "r") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            Logger.warning(f"Corrupt save file found: {path}. Deleting and retrying with template...")
            try:
                os.remove(path)
            except OSError:
                pass
            # Recursive call to try again (which will trigger template copy)
            return cls.load(path)
        
        gm = cls.from_dict(data)
        gm.save_path = path  # ADD: Store which file this player uses
        
        return gm

    
    def ingame_load(self, path):
        if not os.path.exists(path):
            Logger.error(f"No file found: {path}, ignoring load function")
            return False

        with open(path, "r") as f:
            data = json.load(f)
        
            # Update current instance
            self.current_map_key = data["current_map"]

            if data.get("player"):
                from src.entities.player import Player
                spawn_pos = self.player_spawns.get(self.current_map_key)
                if spawn_pos:
                    self.player = Player(spawn_pos.x, spawn_pos.y, self)
                else:
                    self.player = Player.from_dict(data["player"], self)
                
            from src.data.bag import Bag
            self.bag = Bag.from_dict(data.get("bag", {})) if data.get("bag") else Bag([], [])
                
            Logger.info(f"Game state loaded from {path}")
            return True


    def to_dict(self) -> dict[str, object]:
        map_blocks: list[dict[str, object]] = []
        for key, m in self.maps.items():
            block = m.to_dict()
            block["enemy_trainers"] = [t.to_dict() for t in self.enemy_trainers.get(key, [])]
            #ADD Heaaling statue
            if m.healing_statue:
                block['healing_statue'] = self.healing_statue.get(key)
            
            # Add NPC 
            if m.npc_shop:
                block["npc_shop"] = m.npc_shop.to_dict()
            
            map_blocks.append(block)
        return {
            "map": map_blocks,
            "current_map": self.current_map_key,
            "player": self.player.to_dict() if self.player is not None else None,
            "bag": self.bag.to_dict(),
            "achievement": self.achievement,
            "day_time": self.day_time
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "GameManager":
        from src.maps.map import Map
        from src.entities.player import Player
        from src.entities.enemy_trainer import EnemyTrainer
        from src.data.bag import Bag
        from src.additional.day_night_cycle import DayNightCycle
        
        Logger.info("Loading maps")
        maps_data = data["map"]
        maps: dict[str, Map] = {}
        player_spawns: dict[str, Position] = {}
        trainers: dict[str, list[EnemyTrainer]] = {}

        for entry in maps_data:
            path = entry["path"]
            maps[path] = Map.from_dict(entry)
            sp = entry.get("player")
            if sp:
                player_spawns[path] = Position(
                    sp["x"] * GameSettings.TILE_SIZE,
                    sp["y"] * GameSettings.TILE_SIZE
                )
        current_map = data["current_map"]
        gm = cls(
            maps, current_map,
            None, # Player
            {},
            trainers,
            bag=None,
            healing_statue = {},
            day_time = None
        )
        gm.current_map_key = current_map
        
        Logger.info("Loading enemy trainers")
        for m in data["map"]:
            raw_data = m.get("enemy_trainers", None)
            if raw_data:
                gm.enemy_trainers[m["path"]] = [EnemyTrainer.from_dict(t, gm) for t in raw_data]
            
            gm.healing_statue[m["path"]] = m.get('healing_statue', None) # Load statue
            
            #Load npc shop
            npc_data = m.get("npc_shop", None)
            Logger.info(f"Loading NPC for {m['path']}")  
            if npc_data:
                from src.entities.npc import NPC
                gm.maps[m["path"]].npc_shop = NPC.from_dict(npc_data, gm)
            
            #Load achievement_data
            gm.achievement = data.get("achievement", {})
            
            #Load day data
            gm.day_time = data.get("day_time", 8.00)
        
        Logger.info("Loading Player")
        if data.get("player"):
            # Start at spawn position
            spawn_pos = player_spawns.get(current_map)
            if spawn_pos:
                gm.player = Player(spawn_pos.x, spawn_pos.y, gm)
            else:
                # Prevent if no spawn
                gm.player = Player.from_dict(data["player"], gm)
            gm.player_spawns = player_spawns

        Logger.info("Loading bag")
        from src.data.bag import Bag as _Bag
        gm.bag = Bag.from_dict(data.get("bag", {})) if data.get("bag") else _Bag([], [])

        gm.scale_entities() # Start with new size

        return gm
    
    @classmethod
    def set_instance(cls, instance): # make game_manager Global
        cls._instance = instance
    
    @classmethod
    def get_instance(cls): # GET game_manager
        return cls._instance
