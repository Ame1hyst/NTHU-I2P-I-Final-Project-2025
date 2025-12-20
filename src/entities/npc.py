from __future__ import annotations
import pygame
from enum import Enum
from dataclasses import dataclass
from typing import override

from .entity import Entity
from src.sprites import Sprite
from src.core.services import input_manager, scene_manager
from src.core.managers import GameManager
from src.utils import GameSettings, Direction, Position, PositionCamera
import random

class NPC(Entity):
    max_tiles: int | None
    detected: bool
    los_direction: Direction

    @override
    def __init__(
        self,
        x: float,
        y: float,
        game_manager: GameManager,
        max_tiles: int | None = 2,
        facing: Direction | None = None,
        img_path: str  = None, # different img npc
        shop_items: list = None, # assign item
        shop_pokemons: list = None, # assign pokemon
        reset_count: int = 3
        ) -> None:
        super().__init__(x, y, game_manager, img_path)
        self.max_tiles = max_tiles
        self.img_path = img_path
        self.shop_items = shop_items or {}
        self.shop_pokemons = shop_pokemons or {}
        self.reset_count = reset_count
        if facing is None:
            raise ValueError("requires a 'facing' Direction at instantiation")
        self._set_direction(facing)

        self.detected = False
        self.random = True

    @override
    def update(self, dt: float) -> None:
        self._has_los_to_player()
        if self.detected and input_manager.key_pressed(pygame.K_SPACE):
            scene_manager.change_scene('shop')
        self.animation.update_pos(self.position)

    @override
    def draw(self, screen: pygame.Surface, camera: PositionCamera, img_path=None) -> None:
        super().draw(screen, camera, img_path)
        if self.detected:
            pass
        if GameSettings.DRAW_HITBOXES:
            los_rect = self._get_los_rect()
            if los_rect is not None:
                pygame.draw.rect(screen, (255, 255, 0), camera.transform_rect(los_rect), 1)

    def _set_direction(self, direction: Direction) -> None:
        self.direction = direction
        if direction == Direction.RIGHT:
            self.animation.switch("right")
        elif direction == Direction.LEFT:
            self.animation.switch("left")
        elif direction == Direction.DOWN:
            self.animation.switch("down")
        else:
            self.animation.switch("up")
        self.los_direction = self.direction
    def _get_los_rect(self) -> pygame.Rect | None: #  hit box -> shop_scene
        if self.los_direction in [Direction.RIGHT, Direction.LEFT]:
            rect = pygame.Rect(0, 0, self.animation.rect.width*2.5, self.animation.rect.height)
        elif self.los_direction in [Direction.UP, Direction.DOWN]:
            rect = pygame.Rect(0, 0, self.animation.rect.width, self.animation.rect.height*2.5)

        if rect:
            if self.los_direction == Direction.RIGHT:
                rect.midleft = self.animation.rect.center
            elif self.los_direction == Direction.LEFT:
                rect.midright = self.animation.rect.center
            elif self.los_direction == Direction.DOWN:
                rect.midtop = self.animation.rect.center
            else:
                rect.midbottom = self.animation.rect.center
        return rect

    def _has_los_to_player(self) -> None:
        player = self.game_manager.player
        if player is None:
            self.detected = False
            return
        los_rect = self._get_los_rect()
        if los_rect is None:
            self.detected = False
            return
        if player.rect.colliderect(los_rect):
            self.detected = True
        else:
            self.detected = False
    

    @property
    def are_sellout(self):
        return not self.shop_items and not self.shop_pokemons
    
    
    def get_item_sprite(self, item_name):
        sprites = {
            'potion': 'ingame_ui/potion.png',
            'pokeball': 'ingame_ui/ball.png',
            'dfs decrease': 'ingame_ui/options2.png',
            'attack buff': 'ingame_ui/options1.png',
            'defense buff': 'ingame_ui/options6.png',
            'coins': 'ingame_ui/coin.png'
        }
        return sprites.get(item_name.lower())
    
    def ran_stock(self):
        if self.shop_items or self.shop_pokemons:
            return
        
        return self.ran_pokemons(), self.ram_items()
        

    def ran_pokemons(self):
        if self.shop_pokemons:
            return
        
        from src.core import PokemonManager
        pokemon_num = random.randint(3, 6)
        shop_pokemon = {}
        pokemon_manager = PokemonManager()
        pokemon_data = pokemon_manager.get_pokemons()
        base_pokemon = pokemon_manager.get_base_pokemon(pokemon_data)
        for i in range(pokemon_num):
            pokemon = random.choice(base_pokemon)
            evolve = pokemon_data[pokemon].get('evolve', None)
            level = random.randint(5, evolve[1]-1) if evolve else random.randint(5, 29)
            price = self.calculate_pokemon_price(level, evolve)
            shop_pokemon[i] = {
                'name': pokemon,
                'level': level,
                'price': price,
                'sold': False
            }
            shop_pokemon[i]
        return shop_pokemon

    def ram_items(self):
        if self.shop_items:
            return
        
        all_items = ['potion', 'pokeball','dfs decrease', 'attack buff', 'defense buff']
        items_shop = {}
        num_items = random.randint(2, 4)
        item_name = random.sample(all_items, k=num_items)
        for i in range(num_items):
            count = random.randint(5, 10)
            name = item_name[i]
            price = self.calculate_item_price(name, count)
            items_shop[i] = {
                'name': name,
                'count': count,
                'price': price,
                'img_path': self.get_item_sprite(name)
            }
        return items_shop

    def calculate_pokemon_price(self, level, evolve):
        base_price = 100
        price = base_price + (level * 100)

        # Expansive if near evolve
        if evolve:
            evolve_level = evolve[1]
            if level >= evolve_level - 3:
                price = int(price * 1.15)

        return round(price)   
    
    def calculate_item_price(self, item_name, count):
        if item_name.lower() in ['dfs decrease', 'attack buff', 'defense buff']:
            base_price = 80
        elif item_name.lower() == 'potion':
            base_price = 100
        else:
            base_price = 120
        
        discount = 1 - (count - 5) * 0.02  # Smaller discount too
        discount = max(discount, 0.9)  # Max 10% off
    
        random_factor = random.uniform(0.9, 1.1)
        base_price *= random_factor
        return round(base_price * count * discount)

    @classmethod
    @override
    def from_dict(cls, data: dict, game_manager: GameManager) -> "NPC":
        img_path = data.get('img_path', 'character/ow1.png')
        max_tiles = data.get("max_tiles")
        facing_val = data.get("facing")
        facing: Direction | None = None
        if facing_val is not None:
            if isinstance(facing_val, str):
                facing = Direction[facing_val]
            elif isinstance(facing_val, Direction):
                facing = facing_val
        if facing is None:
            facing = Direction.DOWN
        
        shop_items = data.get('shop_items', [])
        shop_pokemons = data.get('shop_pokemon', [])
        reset_count = data.get('reset_count', 3)
        
        return cls(
            data["x"] * GameSettings.TILE_SIZE,
            data["y"] * GameSettings.TILE_SIZE,
            game_manager,
            max_tiles,
            facing,
            img_path,
            shop_items,
            shop_pokemons,
            reset_count
        )

    @override
    def to_dict(self) -> dict[str, object]:
        base: dict[str, object] = super().to_dict()
        base["facing"] = self.direction.name
        base["max_tiles"] = self.max_tiles
        base['img_path'] = self.img_path

        clean_items_data = {}
        for idx, item in self.shop_items.items():
            clean_items_data[idx] = {
                'name': item['name'],
                'count': item['count'],
                'price': item['price'],
                'img_path': item['img_path']
            }
        base['shop_items'] = clean_items_data       
        
        clean_pokemons_data = {}
        for idx, pokemon in self.shop_pokemons.items():
            clean_pokemons_data[idx] = {
                'name': pokemon['name'],
                'level': pokemon['level'],
                'price': pokemon['price'],
                'sold': pokemon['sold']
            }
            
        base['shop_pokemon'] = clean_pokemons_data
        base['reset_count'] = self.reset_count
        return base