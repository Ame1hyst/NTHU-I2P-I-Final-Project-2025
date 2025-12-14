import random
from src.utils.settings import Settings
class EnemyLogic:
    def __init__(self, action_handle):
        self.action_handle = action_handle

    def offline_attack(self):
        attacker = self.action_handle.scene.enemies[self.action_handle.current_enemy]
        attack = random.choice(self.action_handle.battle_logic.pokemon_data[attacker.pokemon]["abilities"])
        return attack

    def online_attack(self):
        pass

    @property
    def attack_handle(self):
        attack = self.offline_attack() if not Settings.IS_ONLINE  else self.online_attack()
        return attack