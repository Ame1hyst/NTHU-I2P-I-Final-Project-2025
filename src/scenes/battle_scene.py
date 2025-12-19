import pygame as pg
from src.utils import GameSettings
from src.sprites import BackgroundSprite
from src.scenes.scene import Scene
from src.interface.components import Button
from src.core.managers import GameManager, PokemonManager, AutoSaveManager
from src.core.services import scene_manager, sound_manager, input_manager, resource_manager
from src.entities.pokemon import Pokemon
from src.battle.battle_logic import BattleLogic
from src.battle.enemy_logic import EnemyLogic
from src.battle.player_logic import PlayerLogic
from src.battle.action_handle import ActionHandle
from typing import override
import random


class BattleScene(Scene):
    background: BackgroundSprite
    game_manager: GameManager
    
    def __init__(self):
        super().__init__()
        self.background = BackgroundSprite("backgrounds/background1.png")

        # Battle setup
        self.enemies = {}
        self.players = {}
        
        self.banner = pg.transform.scale(
            resource_manager.get_image("UI/raw/UI_Flat_Banner04a.png"), 
            (350, 85)
        )
        self.banner_height = self.banner.get_height()
        self.banner_text = pg.Rect(
            (0, GameSettings.SCREEN_HEIGHT-100), 
            (GameSettings.SCREEN_WIDTH, 100)
        )

        # Initialize managers
        self.battle_logic = BattleLogic()
        self.action_handle = ActionHandle(self.battle_logic, self)
        self.player_logic = PlayerLogic(self.action_handle)
        self.enemy_logic = EnemyLogic(self.action_handle)

        # Get pokemon data
        self.pm = PokemonManager.get_instance()
        self.pokemon_data = self.pm.get_pokemons()
        
        # Button setup
        self.attack_button = []
        self.select_button = {
            "fight": Button(
                "UI/raw/UI_Flat_Button01a_4.png", "UI/raw/UI_Flat_Button01a_3.png",
                GameSettings.SCREEN_WIDTH-650, GameSettings.SCREEN_HEIGHT-80, 120, 55,
                lambda: self.action_handle.handle_menu(),
                text='Fight', size=17
            ),
            "bag": Button(
                "UI/raw/UI_Flat_Button01a_4.png", "UI/raw/UI_Flat_Button01a_3.png",
                GameSettings.SCREEN_WIDTH-500, GameSettings.SCREEN_HEIGHT-80, 120, 55,
                lambda: self.player_logic.bag_handle(),
                text='Bag', size=18
            ),
            "catch": Button(
                "UI/raw/UI_Flat_Button01a_4.png", "UI/raw/UI_Flat_Button01a_3.png",
                GameSettings.SCREEN_WIDTH-350, GameSettings.SCREEN_HEIGHT-80, 120, 55,
                lambda: self.player_logic.catch_handle(),
                text='Catch', size=20
            ),
            "run": Button(
                "UI/raw/UI_Flat_Button01a_4.png", "UI/raw/UI_Flat_Button01a_3.png",
                GameSettings.SCREEN_WIDTH-200, GameSettings.SCREEN_HEIGHT-80, 120, 55,
                lambda: scene_manager.change_scene("game"),
                text='Run', size=20
            ),
        }

    @override
    def enter(self) -> None:
        sound_manager.play_bgm("RBY 107 Battle! (Trainer).ogg")
        self.game_manager = GameManager.get_instance()
        self.autosave_manager = AutoSaveManager(self.game_manager)
        
        # Initialize action_handle references
        self.action_handle.game_manager = self.game_manager
                
        # Render new hp
        if not self.players:
            self.render_player_pokemon()
        
        if not self.enemies:
            self.render_enemy_pokemon()

        self.render_button()
                     
    @override
    def exit(self) -> None:
        # Save after fight
        for pokemon_id, pokemon in self.players.items():
            self.game_manager.bag.monsters_data[pokemon_id]['hp'] = pokemon.hp #Hp
            self.game_manager.bag.monsters_data[pokemon_id]['exp'] = pokemon.exp #EXP
            self.game_manager.bag.monsters_data[pokemon_id]['level'] = pokemon.level #level
            self.game_manager.bag.monsters_data[pokemon_id]['name'] = pokemon.pokemon  # Important for evolution!
            self.game_manager.bag.monsters_data[pokemon_id]['max_hp'] = pokemon.max_hp  # Update max_hp too
            
        self.autosave_manager.force_save()
        if scene_manager.next_scene_name == 'game':
            self.action_handle.dialog.reset()  # Prevent caching
            self.battle_logic.reset_buff(self.action_handle.current_player)
            self.battle_logic.reset_buff(self.action_handle.current_enemy)
            self.players.clear()
            self.action_handle.current_player = None
            self.action_handle.reset_enemy()
            
            
            
    @override
    def update(self, dt: float):
        # Update buttons based on state
        if self.action_handle.state == 'menu':
            for button in self.select_button.values():
                button.update(dt)
        else:
            for button in self.attack_button:
                button.update(dt)
        
        # Update dialog and handle game state
        self.action_handle.dialog.update(dt)
        self.action_handle.handle_state()
        self.action_handle.check_catch()
    
    @override
    def draw(self, screen: pg.Surface):
        self.background.draw(screen)
        pg.draw.rect(screen, "#2C292957", self.banner_text)
        
        if not self.battle_logic.battle_over(self.players, self.enemies):
            # Battle ongoing
            self.enemies[self.action_handle.current_enemy].draw(screen)
            self.players[self.action_handle.current_player].draw(screen)
            
            if self.action_handle.state == 'menu':
                for button in self.select_button.values():
                    button.draw(screen)
            else:
                for button in self.attack_button:
                    button.draw(screen)
        else:
            # Battle over
            if input_manager.key_down(pg.K_SPACE):
                scene_manager.change_scene('game')

        # Draw dialog if there's text
        if self.action_handle.dialog.current_text:
            if (self.action_handle.state == 'battle' or 
                (self.action_handle.state == 'menu' and self.action_handle.catching)):
                self.action_handle.dialog.draw(screen)
            
    # --UI Part--
    def render_player_pokemon(self):
        if self.action_handle.current_player is not None and scene_manager.previous_screen_name != 'selected_pokemon':
            return

        team_idx = self.game_manager.player_team_idx
        for idx in team_idx:
            data = self.game_manager.bag.monsters_data[idx]
            pokemon_data = Pokemon(
                pokemon=data['name'],
                hp=data['hp'],
                level=data['level'],
                b_pos=(10, GameSettings.SCREEN_HEIGHT-230),
                c_pos=(300, GameSettings.SCREEN_HEIGHT-380),
                flip=True,
                exp = data['exp']
            )
            pokemon_data.faint = data['hp'] <= 0
            pokemon_data.id = idx
            self.players[pokemon_data.id] = pokemon_data
            
            if self.action_handle.current_player is None and data['hp'] > 0:
                self.action_handle.current_player = pokemon_data.id

    
    def render_enemy_pokemon(self):
        if self.action_handle.current_enemy is not None:
            return
        
        id = 0
        
        # Bush Pokemon (wild)
        if all(not enemy.detected for enemy in self.game_manager.current_enemy_trainers):
            pokemon, level = self.pm.get_rendom_pokemon(self.game_manager.day_state)
            pokemon_data = Pokemon(
                pokemon=pokemon,
                hp=self.pokemon_data[pokemon]['stats']['max_hp'],
                level=level,
                b_pos=(GameSettings.SCREEN_WIDTH-380, 15),
                c_pos=(GameSettings.SCREEN_WIDTH-300, 230)
            )
            pokemon_data.faint = False
            pokemon_data.id = id
            self.enemies[id] = pokemon_data
            self.action_handle.current_enemy = id
            self.action_handle.bush = True
        
        # Enemy Trainers
        else:
            for enemy in self.game_manager.current_enemy_trainers:
                if enemy.detected:
                    for pokemon, level in enemy.pokemon:
                        pokemon_data = Pokemon(
                            pokemon=pokemon,
                            hp=self.pokemon_data[pokemon]['stats']['max_hp'],
                            level=level,
                            b_pos=(GameSettings.SCREEN_WIDTH-380, 15),
                            c_pos=(GameSettings.SCREEN_WIDTH-300, 200)
                        )
                        pokemon_data.faint = False
                        pokemon_data.id = id
                        self.enemies[id] = pokemon_data
                        
                        if self.action_handle.current_enemy is None:
                            self.action_handle.current_enemy = id
                        
                        id += 1
    
    def render_button(self):
        self.attack_button.clear()
        current_pokemon = self.players[self.action_handle.current_player]
        
        for i, attack in enumerate(self.pokemon_data[current_pokemon.pokemon]["abilities"]):
            x = GameSettings.SCREEN_WIDTH - (500-(200*(i//2)))
            y = GameSettings.SCREEN_HEIGHT - (40+(50*(i%2)))
            button = Button(
                "UI/raw/UI_Flat_Button01a_4.png", "UI/raw/UI_Flat_Button01a_3.png",
                x, y, 150, 40,
                lambda atk=attack: self.player_logic.attack_handle(atk),
                text=attack, size=20
            )
            self.attack_button.append(button)
        
        # Back Button
        self.attack_button.append(
            Button(
                "UI/raw/UI_Flat_IconArrow01b.png", "UI/raw/UI_Flat_IconArrow01c.png",
                GameSettings.SCREEN_WIDTH-50, GameSettings.SCREEN_HEIGHT-30, 35, 35,
                lambda: self.action_handle.handle_menu()
            )
        )
    
