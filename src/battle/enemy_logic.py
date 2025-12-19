import random

class EnemyLogic:
    def __init__(self, action_handle):
        self.action_handle = action_handle

    @property
    def attack_handle(self):
        """Pick a random attack from the enemy's available abilities"""
        attacker = self.action_handle.scene.enemies[self.action_handle.current_enemy]
        attack = random.choice(self.action_handle.battle_logic.pokemon_data[attacker.pokemon]["abilities"])
        return attack