import json
import random
class PokemonManager:
    _data = None
    _instance = None
    def __init__(self):
        if not PokemonManager._data:
            self.load()
    
    @classmethod
    def get_instance(cls): # Make it Global
        if cls._instance is None:
            cls._instance = PokemonManager()
        return cls._instance
    
    @classmethod
    def load(cls):
        with open('saves/pokemon_data.json', "r") as f:
            cls._data = json.load(f)
    
    @classmethod
    def get_pokemons(cls):
        return cls._data["pokemons"]

    @classmethod
    def get_attacks(cls):
        return cls._data["attacks"]
    @classmethod
    def get_sprites(cls):
        return cls._data["sprites"]
    
    @classmethod
    def get_element_weakness(cls):
        return cls._data["element_weakness"]
    
    @classmethod
    def get_base_pokemon(cls, pokemon_data:list): # in case if want base pokemon in future
        pokemon_data = cls.get_pokemons()
        base_pokemons = []

        for pokemon, _ in pokemon_data.items():
            is_base = True
            for _, other_data in pokemon_data.items():
                evolve = other_data.get('evolve', None)
                if evolve and evolve[0] == pokemon:
                    is_base = False
                    break
            if is_base:
                base_pokemons.append(pokemon)
        
        return base_pokemons
    @classmethod
    def can_spawn_pokemon(cls, pokemon_name, day_state):
        """Check if Pokemon can spawn at current time"""
        pokemon_data = cls.get_pokemons()
        pokemon = pokemon_data.get(pokemon_name)
        
        if not pokemon:
            return False
        shown = pokemon.get("shown", ["all"])
        return "all" in shown or day_state in shown

    # Example
    @classmethod
    def get_rendom_pokemon(cls, day_state): # Bush pokemon random
        pokemon_data = cls.get_pokemons()
        pokemons = []
        for pokemon_name in pokemon_data.keys():
            if cls.can_spawn_pokemon(pokemon_name, day_state):
                pokemons.append(pokemon_name)
        
        pokemon = random.choice(pokemons)
        pokemon_evolve = pokemon_data[pokemon].get('evolve', None)
        max_level = pokemon_evolve[1] - 1 if pokemon_evolve else 100
        min_level = 5
        for _, other_data in pokemon_data.items():
            evolve = other_data.get('evolve', None)
            if evolve and evolve[0] == pokemon:
                min_level = evolve[1]
                break

        return pokemon, random.randint(min(min_level, max_level), max_level)
    
