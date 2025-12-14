import pygame as pg
from src.utils import load_sound, GameSettings

class SoundManager:
    def __init__(self):
        pg.mixer.init()
        pg.mixer.set_num_channels(GameSettings.MAX_CHANNELS)
        self.current_bgm = None
        self.current_bgm_path = None #for change bgm
        
    def play_bgm(self, filepath: str):
        if self.current_bgm_path == filepath and self.current_bgm:
            return # continue play
        
        if self.current_bgm:
            self.current_bgm.stop()
        
        audio = load_sound(filepath)
        audio.set_volume(GameSettings.AUDIO_VOLUME)
        audio.play(-1)
        self.current_bgm = audio
        self.current_bgm_path = filepath
        
    def pause_all(self):
        pg.mixer.pause()

    def resume_all(self):
        pg.mixer.unpause()
        
    def play_sound(self, filepath, volume=0.7):
        sound = load_sound(filepath)
        sound.set_volume(volume)
        sound.play()
    

    def stop_all_sounds(self):
        pg.mixer.stop()
        self.current_bgm = None
    
    def change_volume(self, val):
        if self.current_bgm:
            self.current_bgm.set_volume(val/100) 