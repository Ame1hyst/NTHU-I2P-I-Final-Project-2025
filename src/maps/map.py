import pygame as pg
import pytmx

from src.utils import load_tmx, Position, GameSettings, PositionCamera, Teleport

class Map:
    # Map Properties
    path_name: str
    tmxdata: pytmx.TiledMap
    # Position Argument
    spawn: Position
    teleporters: list[Teleport]
    # Rendering Properties
    _surface: pg.Surface
    _collision_map: list[pg.Rect]

    #Map obj
    healing_statue: object | None
    npc_shop: object | None

    def __init__(self, path: str, tp: list[Teleport], spawn: Position):
        self.path_name = path
        self.tmxdata = load_tmx(path)
        self.spawn = spawn
        self.teleporters = tp

        pixel_w = self.tmxdata.width * GameSettings.TILE_SIZE
        pixel_h = self.tmxdata.height * GameSettings.TILE_SIZE

        # Prebake the map
        self._surface = pg.Surface((pixel_w, pixel_h), pg.SRCALPHA)
        self._render_all_layers(self._surface)
        # Prebake the collision map
        self._collision_map = self._create_collision_map()

        self._bush = self._create_bush()

        self.healing_statue = None
        self.npc_shop = None

    def update(self, dt: float, player):
        if self.healing_statue:
            self.healing_statue.update(dt, player)
        if self.npc_shop:
            self.npc_shop.update(dt)  

    def draw(self, screen: pg.Surface, camera: PositionCamera):
        screen.blit(self._surface, camera.transform_position(Position(0, 0)))

        if self.healing_statue:
            self.healing_statue.draw(screen, camera)

        if self.npc_shop:
            self.npc_shop.draw(screen, camera)
        
        # Draw the hitboxes collision map and brush
        if GameSettings.DRAW_HITBOXES:
            for rect in self._collision_map:
                pg.draw.rect(screen, (255, 0, 0), camera.transform_rect(rect), 1)
            
            for rect in self._bush:
                pg.draw.rect(screen, (255, 0, 0), camera.transform_rect(rect), 1)
        
    def check_collision(self, rect: pg.Rect) -> bool:
        for mrect in self._collision_map:
            if rect.colliderect(mrect):
                return True
        return False
    
    def check_bush(self, rect: pg.Rect) -> bool:
        for brect in self._bush:
            if rect.colliderect(brect):
                return True
        return False
        
    def check_teleport(self, pos: Position) -> Teleport | None:
        px = int(pos.x) // GameSettings.TILE_SIZE
        py = int(pos.y) // GameSettings.TILE_SIZE
        for tp in self.teleporters:
            tx, ty = tp.pos.x // GameSettings.TILE_SIZE, tp.pos.y // GameSettings.TILE_SIZE
            if tx == px and ty == py:
                return tp
        return None        
    
    def _render_all_layers(self, target: pg.Surface) -> None:
        for layer in self.tmxdata.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                self._render_tile_layer(target, layer)
            # elif isinstance(layer, pytmx.TiledImageLayer) and layer.image:
            #     target.blit(layer.image, (layer.x or 0, layer.y or 0))
 
    def _render_tile_layer(self, target: pg.Surface, layer: pytmx.TiledTileLayer) -> None:
        for x, y, gid in layer:
            if gid == 0:
                continue
            image = self.tmxdata.get_tile_image_by_gid(gid)
            if image is None:
                continue

            image = pg.transform.scale(image, (GameSettings.TILE_SIZE, GameSettings.TILE_SIZE))
            target.blit(image, (x * GameSettings.TILE_SIZE, y * GameSettings.TILE_SIZE))
    
    def _create_collision_map(self) -> list[pg.Rect]:
        rects = []
        for layer in self.tmxdata.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer) and ("collision" in layer.name.lower() or "house" in layer.name.lower()):
                for x, y, gid in layer:
                    if gid != 0:
                        rects.append(pg.Rect(x*GameSettings.TILE_SIZE, y*GameSettings.TILE_SIZE, GameSettings.TILE_SIZE, GameSettings.TILE_SIZE))
                        
        return rects
    
    def _create_bush(self) -> list[pg.Rect]:
        rects = []
        for layer in self.tmxdata.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer) and "pokemonbush" in layer.name.lower():
                for x, y, gid in layer:
                    if gid != 0:
                        rects.append(pg.Rect(x*GameSettings.TILE_SIZE, y*GameSettings.TILE_SIZE, GameSettings.TILE_SIZE, GameSettings.TILE_SIZE))
                        
        return rects

    @classmethod
    def from_dict(cls, data: dict) -> "Map":
        tp = [Teleport.from_dict(t) for t in data["teleport"]]
        pos = Position(data["player"]["x"] * GameSettings.TILE_SIZE, data["player"]["y"] * GameSettings.TILE_SIZE)
        m = cls(data["path"], tp, pos)
        
        if data.get('healing_statue', None): # Check if have OBJ
            from src.additional.healing_statue import HealStatue
            n_data = data.get('healing_statue')
            m.healing_statue = HealStatue(**n_data)
        
        return m

    def to_dict(self):
        return {
            "path": self.path_name,
            "teleport": [t.to_dict() for t in self.teleporters],
            "player": {
                "x": self.spawn.x // GameSettings.TILE_SIZE,
                "y": self.spawn.y // GameSettings.TILE_SIZE,
            }
        }
