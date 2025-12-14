from src.battle.action_handle import ActionHandle
from src.core.managers import GameManager
from src.core.services import scene_manager

class PlayerLogic:
    def __init__(self, action_handle: ActionHandle):
        self.action_handle = action_handle
        self.game_manager = GameManager.get_instance()
        
        pass

    def attack_handle(self, attack):
        self.action_handle.player_attack(attack)

    def catch_handle(self):
        self.action_handle.catch_pokemon()

    def bag_handle(self):
        scene_manager.change_scene("bag")


