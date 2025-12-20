import pygame as pg
from src.utils import load_sound, GameSettings

class SoundManager:
    def __init__(self):
        pg.mixer.init()
        pg.mixer.set_num_channels(GameSettings.MAX_CHANNELS)
        self.current_bgm = None
        self.current_bgm_path = None #for change bgm
        
    def play_bgm(self, filepath: str, volume: float = GameSettings.AUDIO_VOLUME):
        if self.current_bgm_path == filepath and self.current_bgm:
            # Update volume even if it's the same track (in case volume changed)
            self.current_bgm.set_volume(volume)
            return # continue play
        
        if self.current_bgm:
            self.current_bgm.stop()
        
        from src.core.services import resource_manager # prevent circular import
        audio = resource_manager.get_sound(filepath)
        audio.set_volume(volume)
        audio.play(-1)
        self.current_bgm = audio
        self.current_bgm_path = filepath
        
    def pause_all(self):
        pg.mixer.pause()

    def resume_all(self):
        pg.mixer.unpause()
        
    def play_sound(self, filepath, volume=GameSettings.SOUND_VOLUMN):
        from src.core.services import resource_manager # prevent circular import
        sound = resource_manager.get_sound(filepath)
        sound.set_volume(volume)
        sound.play()
    

    def stop_all_sounds(self):
        pg.mixer.stop()
        self.current_bgm = None
    
    def change_volume(self, val):
        if self.current_bgm:
            self.current_bgm.set_volume(val/100) 