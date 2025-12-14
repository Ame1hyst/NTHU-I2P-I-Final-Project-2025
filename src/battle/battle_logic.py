from src.core.managers import PokemonManager
import random
class BattleLogic:
    def __init__(self):
        self.pm = PokemonManager.get_instance()
        self.pokemon_data = self.pm.get_pokemons()
        self.attack_data = self.pm.get_attacks()
        self.element_weakness = self.pm.get_element_weakness()

        self.status_effects = {} # id :{value: max_stat: turn}

    # --Level up logic--
    def atk_exp(self, attacker, target, damage_dealt):
        # EXP from doing damage
        damage_percent = damage_dealt / target.max_hp #hp_remove from target
        base_exp = target.level * 25 * damage_percent
        
        # Level diff multiplier
        level_diff = target.level - attacker.level
        if level_diff > 0:
            # Target is higher level
            level_multiplier = 1 + (level_diff * 0.15)
        else:
            # Target is lower level
            level_multiplier = max(1 + (level_diff * 0.1), 0.2)
        
        # EXP from defeating enemy
        kill_bonus = 0
        if target.hp <= 0:
            kill_bonus = int(100 * level_multiplier)
        
        total_exp = int(base_exp * level_multiplier) + kill_bonus
        return max(total_exp, 1)

    
    # --Item logic--
    def init_pokemon_status(self, pokemon_id):
        if pokemon_id not in self.status_effects:
            self.status_effects[pokemon_id] = {
                'attack buff': {'value': 0, 'max_stat': 3, 'turn': 0},
                'dfs decrease': {'value': 0, 'max_stat': 5, 'turn': 0}
            }    
    def set_buff(self, buff, pokemon_id):
        if not buff:
            return
        
        self.init_pokemon_status(pokemon_id)
        pokemon_status = self.status_effects[pokemon_id]
        
        max_buff = pokemon_status[buff]['max_stat']
        if buff == 'attack buff':
            new_value =  min(pokemon_status[buff]['value']+3, max_buff) # Limit to the Max
        elif buff == 'dfs decrease':
            new_value =  min(pokemon_status[buff]['value']+5, max_buff) # Limit to the Max        
        pokemon_status[buff]['value'] = new_value
        pokemon_status[buff]['turn'] = 4 # Remian only 3 turn
    
    def apply_buff(self, pokemon_id):
        if pokemon_id not in self.status_effects:
            return 0, 0
        status = self.status_effects[pokemon_id]
        
        # Add buff
        atk_buff = status['attack buff']['value']
        dfs_buff = status['dfs decrease']['value']
        
        return atk_buff, dfs_buff   
    
    def count_turn(self, pokemon_id):
        if pokemon_id not in self.status_effects:
            return []
        
        text = []
        pokemon_status = self.status_effects[pokemon_id]
        if pokemon_status['attack buff']['value'] > 0 and pokemon_status['attack buff']['turn'] > 0:
            pokemon_status['attack buff']['turn'] -= 1
            if pokemon_status['attack buff']['turn'] == 0:
                pokemon_status['attack buff']['value'] = 0
                text.append("Attack buff wore off")
                self.reset_buff(pokemon_id)

        if pokemon_status['dfs decrease']['value'] > 0 and pokemon_status['dfs decrease']['turn'] > 0:
            pokemon_status['dfs decrease']['turn'] -= 1
            if pokemon_status['dfs decrease']['turn'] == 0:
                pokemon_status['dfs decrease']['value'] = 0
                text.append("Defense debuff wore off")
                self.reset_buff(pokemon_id)

        return text   
      
    
    def reset_buff(self, pokemon_id):
        if pokemon_id in self.status_effects:
            self.status_effects[pokemon_id] = {
            'attack buff': {'value': 0, 'max_stat': 3, 'turn': 0},
            'dfs decrease': {'value': 0, 'max_stat': 5, 'turn': 0}
            }    
    # --Battle logic--
    def handle_attack(self, attacker, target, attack_name, attacker_side, attacker_id, target_id):
        buff_atk, _ = self.apply_buff(attacker_id)
        _, buff_dfs = self.apply_buff(target_id)
        damages, text = self.calculate_atk(attack_name, target, attacker, buff_atk, buff_dfs)        
        target.hp = max(target.hp - damages, 0)
        
        texts = []
        if text:
            texts.append(text)
        texts.append(f"{attacker_side}'s {attacker.pokemon} use {attack_name} to {target.pokemon} make damage {damages}")
        
        if attacker.exp is not None:
            attacker.exp += self.atk_exp(attacker, target, damages)
            level_up, evolved = attacker.add_level(attacker.exp)
            if level_up:
                texts.append(f"{attacker.pokemon} level up")
            
            if evolved:
                texts.append(f"{attacker.pokemon} is ready to evolve!")    
        return texts
            
    def calculate_atk(self, attack, target, attacker, buff_atk, buff_dfs):
        base_dmg = self.attack_data[attack]['damage']
        attack_element = self.attack_data[attack]["element"]
        target_element = self.pokemon_data[target.pokemon]['stats']["element"]

        atk_total = attacker.atk + buff_atk
        dfs_total = max(target.dfs - buff_dfs, 1)

        level_multiplier = 1 + (attacker.level / 50)
        stat_multiplier = (atk_total * 1.5) / (dfs_total + 5)
        dmg = base_dmg * level_multiplier * stat_multiplier

        text = None
        
        if attack_element in self.element_weakness[target_element]:
            text = "Very Effective"
            dmg*=1.5
        
        elif attack_element == target_element:
            text = "Not THAT Effective"
            dmg*=0.5
        
        return int(dmg), text
    
    def is_faint(self, pokemon):
        return pokemon.hp <= 0
    
    def get_next_pokemon(self, pokemon_dict:dict):
        for id, data in pokemon_dict.items():
            if not data.faint:
                return id
        return None    
            
    def battle_over(self, players:dict, enemies:dict):
        return all(data.faint for data in players.values()) or all(data.faint for data in enemies.values()) or not enemies

    def calculate_coins_count(self, target):
        base = int(10 + (target.level ** 1.3) * 4)
        rng = random.randint(-2, int(target.level * 0.3) + 2)
        return max(1, base + rng)
