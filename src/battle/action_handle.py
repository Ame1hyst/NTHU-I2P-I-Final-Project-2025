from src.interface.components.dialog import Dialog
from src.core.managers import PokemonManager
import random

class ActionHandle:
    def __init__(self, battle_logic, battle_scene):
        self.current_player = None
        self.current_enemy = None
        self.current_turn = 'player' #Turn-base system
        self.previous_turn = None
        self.state = 'menu' #Button system

        self.battle_logic = battle_logic

        self.scene = battle_scene
        self.dialog = Dialog(self.scene.banner_text, (10, 50), speed=50, size=20, color="White", max_char=30)

        self.poke_path = PokemonManager.get_sprites()
        self.poke_info = PokemonManager.get_pokemons()
        self.bush = False
        self.catching = False

    # --State Handle--
    def handle_menu(self):
        self.state = 'menu' if self.state == 'battle' else 'battle'
        return self.state
    
    def switch_turn(self):
        if self.previous_turn == 'player':
            self.current_turn = 'enemy'
        elif self.previous_turn == 'enemy':
            self.current_turn = 'player'
    
    def handle_state(self):
        if self.battle_logic.battle_over(self.scene.players, self.scene.enemies):
            return      
        
        if self.current_turn == 'enemy':
            attack = self.scene.enemy_logic.attack_handle
            self.enemy_attack(attack)


    def handle_fainted_pokemon(self, pokemon, team_dict, team_name):
        texts = []

        if not self.battle_logic.is_faint(pokemon):
            return texts  # Do nothing

        texts.append(f"{pokemon.pokemon} is faint")
        pokemon.faint = True

        if team_name == 'Enemy':
            coins_count = self.battle_logic.calculate_coins_count(pokemon)
            self.scene.game_manager.bag.items_data[0]['count'] += coins_count
            texts.append(f"Player receive {coins_count}")

        # switch if this was the active Pokémon
        if (team_name == "Player" and self.current_player != pokemon.id) or (team_name == "Enemy" and self.current_enemy != pokemon.id):
            return texts

        next_pokemon = self.battle_logic.get_next_pokemon(team_dict)
        if next_pokemon is not None:
            if team_name == 'Player':
                self.current_player = next_pokemon
                self.scene.render_button()
            else:
                self.current_enemy = next_pokemon

            texts.append(f"{team_name} sent {team_dict[next_pokemon].pokemon}")
        else:
            texts.extend([f"All {team_name} Pokemon Down", "Press space to quit"])

        return texts    

    def enemy_attack(self, attack):
        if self.current_turn != 'enemy':
            return

        attacker, target = self.scene.enemies[self.current_enemy], self.scene.players[self.current_player]
        texts = self.battle_logic.handle_attack(attacker, target, attack, "Enemy", self.current_enemy, self.current_player)   
        self.previous_turn = 'enemy'
        self.current_turn = 'waiting' #Delay fight
        
        #Count buff turn
        texts.extend(self.battle_logic.count_turn(self.current_enemy))

        
        texts.extend(self.handle_fainted_pokemon(target, self.scene.players, "Player"))       
        self.dialog.add_sequence(texts, callback=self.switch_turn)                                   
    
    def player_attack(self, attack):
        if self.current_turn != 'player':
            return
        
        attacker, target = self.scene.players[self.current_player], self.scene.enemies[self.current_enemy]
        texts = self.battle_logic.handle_attack(attacker, target, attack, "Player", self.current_player, self.current_enemy)       
        self.previous_turn = 'player'
        self.current_turn = 'waiting' #Delay fight
        
        #Count buff turn
        texts.extend(self.battle_logic.count_turn(self.current_player))
        
        target.faint = target.hp <= 0            
        texts.extend(self.handle_fainted_pokemon(target, self.scene.enemies, "Enemy"))
        self.dialog.add_sequence(texts, callback=self.switch_turn)


    def reset_enemy(self):
        self.scene.enemies.clear()
        self.current_enemy = None
        self.current_turn = 'player'
        self.previous_turn = None
        self.state = 'menu'
        self.catching = False 


    def check_catch(self):
        if not self.catching:
            return
        
        # If pokemon finished catch animation
        if self.current_enemy in self.scene.enemies:
            pokemon = self.scene.enemies[self.current_enemy]
            if not pokemon.catching:  # Animation finished
                del self.scene.enemies[self.current_enemy]
                self.catching = False
                self.current_enemy = None

    def catch_pokemon(self):
        if not self.bush or self.battle_logic.battle_over(self.scene.players, self.scene.enemies) or self.catching:
            return

        for item in self.scene.game_manager.bag.items_data:
            if item['name'].lower() == 'pokeball' and item['count'] > 0 and random.randint(0, 1):
                catch_pokemon = self.scene.enemies[self.current_enemy]
                
                self.scene.game_manager.bag.monsters_data.append({
                    "name": catch_pokemon.pokemon,
                    "hp": catch_pokemon.hp,
                    "max_hp": self.poke_info[catch_pokemon.pokemon]['stats']['max_hp'],
                    "level": catch_pokemon.level,
                })                
                # Start catch animation
                catch_pokemon.catching = True
                self.catching = True
                self.state = 'battle'
                item['count'] -= 1
                
                coins_count = self.battle_logic.calculate_coins_count(catch_pokemon)
                self.scene.game_manager.bag.items_data[0]['count'] += coins_count
                
                self.dialog.add_sequence(["Pokemon caught!", f"Player receive {coins_count}", "Press space to quit"])
                break
            
        else:
            self.state = 'battle'
            self.current_turn = 'waiting'
            self.previous_turn = 'player'
            self.dialog.add_sequence(["Can not catch pokemon"], callback=self.switch_turn)