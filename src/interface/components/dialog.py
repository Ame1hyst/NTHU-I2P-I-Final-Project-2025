import pygame as pg
from src.core.services import resource_manager

class Dialog():
    def __init__(self, rect: pg.Rect, pos:tuple, speed=0, font='Minecraft.ttf', size=20, color="#000000", max_char=30):
        self.rect = rect
        self.pos = pos
        self.speed = speed

        self.font = resource_manager.get_font(font, size)
        self.color = color
        self.text = []
        # Play Current Dialog
        self.current_text = None
        self.wrapped_text = None
        self.max_char = max_char
        self.index = 0
        self.char_index = 0
        
        # Q system
        self.queue = []
        self.queue_active = False
        self.queue_call_back = None # Func after dialog finish
        self.dialog_timer = 0 # Delay when blit
        

    def draw(self, screen, camera=None):
        if camera:
            self.rect = camera.transform_rect(self.rect)
        if self.speed:
            text = self.animation()
        else:
            text = " ".join(self.wrapped_text)
        text_surf = self.font.render(text, True, self.color) 
        screen.blit(text_surf, (self.rect.x + self.pos[0], self.rect.y + self.pos[1]))
        
    
    def add_text(self, text:list): #For manual
        if isinstance(text, str):
            text = [text]
        text = [t for t in text if t is not None]

                
        if self.index == 0 and not self.current_text:
            self.current_text = self.text[0]
            self.wrapped_text = self.wrap_text(self.current_text, self.max_char)
            self.char_index = 0
    
    def add_sequence(self, text:list, callback=None): # For auto Dialog              
        if isinstance(text, str):
            text = [text]
        text = [t for t in text if t is not None]

        self.queue.extend(text)
        self.queue_active = True
        self.queue_call_back = callback
        
        if not self.current_text:
            self.load_next_sequence()
            self.queue_active = True


    def load_next_sequence(self):        
        text = self.queue.pop(0)
        self.text = [text] # Clear unused
        self.index = 0
        self.current_text = text
        self.wrapped_text = self.wrap_text(text, self.max_char)
        self.char_index = 0
    

    def update(self, dt):
        self.char_index += dt*self.speed
        if self.dialog_timer <= 70:
            self.dialog_timer += dt*self.speed
            return
        
        if self.queue_active and self.is_done():
            if self.queue:
                self.dialog_timer = 0
                self.load_next_sequence()
            else:
                if self.queue_call_back:
                    self.queue_call_back()
                    self.queue_call_back = None
                self.queue_active = False

    def animation(self):
        full_text = " ".join(self.wrapped_text)
        index = min(int(self.char_index), len(full_text))
        return full_text[:index]
    
    def next_dialog(self):            
        if self.index < len(self.text)-1:
            self.index += 1
            self.current_text = self.text[self.index]
            self.wrapped_text = self.wrap_text(self.current_text, self.max_char)
            self.char_index = 0
             
    
    def wrap_text(self, text, max_char):
        if isinstance(text, list):
            return [self.wrap_text(item, max_char) for item in text]
        
        words = text.split()
        line = []
        current_line = ""

        # Make sentence
        for word in words:
            if current_line:
                sentence = current_line + " " + word
            else:
                sentence = word
            
            #Check max
            if len(sentence) <= max_char:
                current_line = sentence
            else:
                line.append(current_line)
                current_line = word
        # If it left
        if current_line:
            line.append(current_line)
        return line

    def is_done(self):
        if self.speed == 0 or not self.current_text:
            return True
        if self.text:
            full_text = " ".join(self.wrapped_text)
            return int(self.char_index) >= len(full_text)
        return False
    
    def reset(self):
        self.text = []
        # Play Current Dialog
        self.current_text = None
        self.wrapped_text = None
        self.index = 0
        self.char_index = 0
        
        # Q system
        self.queue = []
        self.queue_active = False
        self.queue_call_back = None
        self.dialog_timer = 0
