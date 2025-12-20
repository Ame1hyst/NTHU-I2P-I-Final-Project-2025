import pygame as pg

from src.utils import GameSettings
from src.sprites import BackgroundSprite
from src.scenes.scene import Scene
from src.interface.components import Button
from src.core.managers import GameManager
from src.core.services import scene_manager, sound_manager, input_manager, resource_manager
from typing import override

class SettingScene(Scene):
    # Background Image
    background: BackgroundSprite


    game_manager: GameManager
    
    def __init__(self):
        super().__init__()
        self.background = BackgroundSprite("UI/raw/UI_Flat_Frame03a.png", size=(GameSettings.SCREEN_WIDTH//2, GameSettings.SCREEN_HEIGHT*2//3), cpos=(GameSettings.SCREEN_WIDTH * 1 // 4, GameSettings.SCREEN_HEIGHT* 1// 6))
        self.game_manager = GameManager.get_instance()
        
        #Button
        px, py = GameSettings.SCREEN_WIDTH // 2, GameSettings.SCREEN_HEIGHT* 3// 5
        self.button = {
            "back": Button(
            "UI/button_back.png", "UI/button_back_hover.png",
            px, py, 70, 70,
            lambda: scene_manager.change_scene("menu")
        ),
            "x": Button(
            "UI/button_x.png", "UI/button_x_hover.png",
            px+270, py-300, 35, 35,
            lambda: scene_manager.change_scene(scene_manager.previous_screen_name)
        ),
            "back": Button(
            "UI/button_back.png", "UI/button_back_hover.png",
            px, py, 70, 70,
            lambda: scene_manager.change_scene("menu")
        ),
            "save": Button( 
            "UI/button_save.png", "UI/button_save_hover.png", 
            px-100, py, 70, 70, lambda: self.game_manager.save(path="saves/game0.json")
        ),
            "load": Button(
            "UI/button_load.png", "UI/button_load_hover.png",
            px-200, py, 70, 70,
            lambda: self.game_manager.ingame_load(path="saves/game0.json")
        )
        }
        self.set_vols = {
            "bar": {
                "img": pg.transform.scale(resource_manager.get_image("UI/raw/UI_Flat_BarFill01g.png"), (550, 20)),
                "pos": (px*3//5-20, py*2//3)
            },
            "hold_button": {
                "img": pg.transform.scale(resource_manager.get_image("UI/raw/UI_Flat_Button01a_4.png"), (25, 25)),
                "pos": (px*3//2-50, py*2//3-5)
            },
            "mute_button": {
                "img": (
                    pg.transform.scale(resource_manager.get_image("UI/raw/UI_Flat_ToggleOff03a.png"), (50, 50)),
                    pg.transform.scale(resource_manager.get_image("UI/raw/UI_Flat_ToggleOn03a.png"), (70, 50))
                ),
                "pos": (px*3//5-20, py*2//3+50),
                "state": False 
            }
        }
        for name, pic in self.set_vols.items():
            if name == "mute_button":
                pic["rect"] = pic["img"][0].get_rect(topleft=pic["pos"])
            else:
                pic["rect"] = pic["img"].get_rect(topleft=pic["pos"])
        
        self.font = resource_manager.get_font('Minecraft.ttf', 40)

    @override  
    def enter(self) -> None:
        sound_manager.play_sound('open-bag-sound.mp3')
        self.vol_num = int(GameSettings.AUDIO_VOLUME*100)
        pass

    @override
    def exit(self) -> None:
        sound_manager.play_sound('open-bag-sound.mp3')
        GameSettings.AUDIO_VOLUME = self.vol_num/100
        self.set_vols["mute_button"]["state"] = False
        pass

    @override
    def update(self, dt: float) -> None:
        if input_manager.key_pressed(pg.K_SPACE):
            scene_manager.change_scene("menu")
            return
        for button in self.button.values():
            button.update(dt)
    
    @override
    def draw(self, screen: pg.Surface) -> None:
        if scene_manager.previous_screen_surf:
            screen.blit(scene_manager.previous_screen_surf, (0,0))
        overlay = pg.Surface((screen.get_size()), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        screen.blit(overlay, (0,0))
        
        self.background.draw(screen)
        for button in self.button.values():
            button.draw(screen)
        
        self.set_volumn(screen)
    
    def set_volumn(self, screen):
        self.set_vols['hold_button']['rect'].x = self.set_vols['bar']['rect'].x + (self.vol_num * 547 / 100) - 10
        for name, pic in self.set_vols.items():
            if name == "mute_button":
                # Draw mute button due to state
                img = pic["img"][1] if pic["state"] else pic["img"][0]
                screen.blit(img, pic["rect"])
            else:
                screen.blit(pic["img"], pic["rect"])  
        if input_manager.mouse_down(1) and self.set_vols['bar']['rect'].collidepoint(input_manager.mouse_pos):
            self.set_vols['hold_button']['rect'].x = input_manager.mouse_pos[0]-10
            self.vol_num = int(((self.set_vols['hold_button']['rect'].x-self.set_vols['bar']['rect'].x) + 10) / 547 * 100)
            sound_manager.change_volume(self.vol_num)
        
        if input_manager.mouse_pressed(1) and self.set_vols['mute_button']['rect'].collidepoint(input_manager.mouse_pos):
            self.set_vols["mute_button"]["state"] = not self.set_vols["mute_button"]["state"]
            if self.set_vols["mute_button"]["state"]:
                sound_manager.pause_all()
            else: sound_manager.resume_all()
        
        vol_surf = self.font.render(f"Volume: {str(self.vol_num)}", True, '#313647')
        vol_rect = vol_surf.get_rect(topleft = (360, 220))
        screen.blit(vol_surf, vol_rect)