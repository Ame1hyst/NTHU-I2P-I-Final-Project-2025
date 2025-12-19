from src.maps.map import Map
from src.interface.components.button import Button
from src.core import GameManager
from src.core.services import resource_manager
from src.utils import load_tmx, Position, GameSettings, PositionCamera, Teleport
import pygame as pg
from collections import deque
class Navigation:
    game_manager: GameManager

    def __init__(self, game_manager):
        self.avaliable_place = {}
        self.selected_place = None 

        self.game_manager = game_manager

        large_font = resource_manager.get_font('Minecraft.ttf', 20)
        self.mid_font = resource_manager.get_font('Minecraft.ttf', 15)
        self.small_font = resource_manager.get_font('Minecraft.ttf', 10)

        self.title_surf = large_font.render("Destination:", True, "#D2DFFD")

        self.padding = 25

        # Panel ui
        self.panel_rect = None
        
        # Path store
        self.path= []

    def draw(self, screen, map_pos:tuple, map_size:tuple):
        if not self.panel_rect:
            self.panel_rect = pg.rect.Rect(map_pos[0]+map_size[0], map_pos[1], 170, map_size[1])
        
        pg.draw.rect(screen, "#514E4E", self.panel_rect)
        screen.blit(self.title_surf, (self.panel_rect.left + 10, self.panel_rect.top + 10))


        for map_data in self.avaliable_place.values():
            if 'button' in map_data:
                map_data['button'].draw(screen)

    def update(self, dt):
        for map_data in self.avaliable_place.values():
            if 'button' in map_data:
                map_data['button'].update(dt)
        self.update_remian_path()

# ==render--
    def render_ui(self, map_pos, map_size):
        if not self.game_manager.current_map:
            return
        
        if self.avaliable_place:
            return
        
        self.render_place()
        self.render_button(map_pos, map_size)
    
    def render_place(self):
        current_map = self.game_manager.current_map
        if current_map.healing_statue:
            self.avaliable_place["healing statue"] = {
                'name': "Healing Statue",
                'pos': (current_map.healing_statue.statue_rect.x, current_map.healing_statue.statue_rect.y),
            }
        
        if current_map.npc_shop:
            self.avaliable_place["shop"] = {
                'name': "Shop",
                'pos': (current_map.npc_shop.position.x, current_map.npc_shop.position.y),
            }
        
        for tp in current_map.teleporters:
            name = tp.destination.replace('.tmx', '').title()
            if name not in self.avaliable_place:
                self.avaliable_place[name.lower()] = {
                    'name': name,
                    'pos': (tp.pos.x, tp.pos.y),
                }      
            
    def render_button(self, map_pos, map_size):
        panel_x = map_pos[0] + map_size[0] + 10
        panel_y = map_pos[1]
        
        height = 50
        start_y = panel_y + 40          
        
        for i, map_data in enumerate(self.avaliable_place.values()):
            x = panel_x
            y = start_y + i * (height + self.padding)
            map_data['button'] = Button(
            "UI/raw/UI_Flat_Button01a_2.png", "UI/raw/UI_Flat_Button01a_1.png",
            x, y, 140, height,
            lambda p=map_data['pos']: self.go_to_pos(p),
            text=map_data['name'], size=15, color="#000000"
            )

# --UI--   
    def draw_path(self, screen, camera:PositionCamera):
        if not self.path or len(self.path) < 2:
            return
        
        points = []
        tile_size = self.game_manager.get_tile_size()
        for tile_x, tile_y in self.path:
            # W coord
            world_x = tile_x * tile_size + tile_size // 2
            world_y = tile_y * tile_size + tile_size // 2
            
            screen_pos = camera.transform_position(Position(world_x, world_y))
            points.append(screen_pos)        
        
        # Draw the path line
        if len(points) >= 2:
            pg.draw.lines(screen, "yellow", False, points, 5)

# --BFS + other logic--
    def calculate_path(self, start, destination):
        if not self.game_manager.player:
            return []
        
        queue = deque([start])

        came_from = {}
        came_from[start] = None

        while queue:
            current = queue.popleft()

            if current == destination:
                break

            for nxt in self.four_direction_path(*current, destination):
                if nxt not in came_from:
                    queue.append(nxt)
                    came_from[nxt] = current

        # reconstruct path
        if destination not in came_from:
            return []  # Cannot go

        path = []
        cur = destination
        while cur:
            path.append(cur)
            cur = came_from[cur]

        path.reverse()
        return path
    
    def can_walk(self, tile_x: int, tile_y, destination: tuple):
        current_map = self.game_manager.current_map
        tile_size = self.game_manager.get_tile_size()

        #Check bounds
        if tile_x < 0 or tile_y < 0:
            return False
        if tile_x >= current_map.tmxdata.width or tile_y >= current_map.tmxdata.height:
            return False
        
        for tp in current_map.teleporters:
            tp_tile_x = int(tp.pos.x // tile_size)
            tp_tile_y = int(tp.pos.y // tile_size)
            
            if tile_x == tp_tile_x and tile_y == tp_tile_y:
                # Only allow if this IS the destination
                if destination and tile_x == destination[0] and tile_y == destination[1]:
                    return True
                return False        
        #Check collision
        rect = pg.Rect(tile_x * tile_size, tile_y * tile_size, tile_size, tile_size)
    
        return not self.game_manager.check_collision(rect)
    
    def find_walk_dest(self, dest):
        if self.can_walk(*dest, dest):
            return dest

        for dx, dy in [(0,1),(0,-1),(1,0),(-1,0)]:
            nx, ny = dest[0]+dx, dest[1]+dy
            if self.can_walk(nx, ny, dest):
                return (nx, ny)

        return None
    
    def four_direction_path(self, tile_x, tile_y, destination: tuple):
            path = []         
            for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:  # up down left right
                nx, ny = tile_x + dx, tile_y + dy
                if self.can_walk(nx, ny, destination):
                    path.append((nx, ny))             
            
            return path
    
    def go_to_pos(self, pos:tuple):
        self.selected_place = pos 
        tile_size = self.game_manager.get_tile_size()
        
        if not self.game_manager.player:
            return
        
        
        player = self.game_manager.player
        
        #pixel -> tile coords
        start = (int(player.position.x/ tile_size), int(player.position.y // tile_size))
        end = (int(pos[0] // tile_size),int(pos[1] // tile_size))
        
        end = self.find_walk_dest(end)
        if not end:
            self.path = []
            return
        
        #calculate path
        self.path = self.calculate_path(start, end)
        print(f"Path to {pos}: {len(self.path)} steps")
    
             
    def update_remian_path(self):
        if not self.path or not self.game_manager.player:
            return
        tile_size = self.game_manager.get_tile_size()
        player_tile = (
            self.game_manager.player.position.x // tile_size, 
            self.game_manager.player.position.y // tile_size
            )

        if player_tile in self.path:
            idx = self.path.index(player_tile)

            # slice remove path
            self.path = self.path[idx:]

        # at destination
        if len(self.path) <= 2:
            self.reset() 
    
    def reset(self):
        self.avaliable_place.clear()
        self.panel_rect = None
        self.path = []
        self.selected_place = None


