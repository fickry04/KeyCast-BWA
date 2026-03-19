import json
import os

# =============================================================================
# CONFIGURATION CLASS
# =============================================================================

class AppConfig:
    """Persistent configuration storage."""
    CONFIG_FILE = "app_config.json"
    
    def __init__(self):
        self.config = {
            'board_region': None,
            'attack_button': None,
            'delete_button': None,
            'target_window': None,
            'threshold': 0.75,
            'scale_factors': [0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.5],
            'auto_rescan': True,
            'rescan_delay': 0.5
        }
        self.load()
        
    def load(self):
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, 'r') as f:
                    saved = json.load(f)
                    self.config.update(saved)
            except Exception as e:
                print(f"Error loading config: {e}")
                
    def save(self):
        try:
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")

# =============================================================================
# STATE MANAGEMENT
# =============================================================================

class AppState:
    def __init__(self, config: AppConfig):
        self.config = config
        self.letter_positions = {}
        self.used_tiles = {}
        self.typed_letters = []
        self.board_region = None
        self.attack_button_position = None
        self.delete_button_position = None
        self.load_from_config()
        
    def load_from_config(self):
        if self.config.config['board_region']:
            self.board_region = tuple(self.config.config['board_region'])
        if self.config.config['attack_button']:
            self.attack_button_position = tuple(self.config.config['attack_button'])
        if self.config.config['delete_button']:
            self.delete_button_position = tuple(self.config.config['delete_button'])
            
    def save_to_config(self):
        self.config.config['board_region'] = list(self.board_region) if self.board_region else None
        self.config.config['attack_button'] = list(self.attack_button_position) if self.attack_button_position else None
        self.config.config['delete_button'] = list(self.delete_button_position) if self.delete_button_position else None
        self.config.save()
        
    def reset_tiles(self):
        for letter in self.used_tiles:
            self.used_tiles[letter] = [False] * len(self.used_tiles[letter])
        self.typed_letters = []
        
    def get_available_tile(self, letter: str):
        letter = letter.upper()
        if letter not in self.used_tiles:
            return None
        for i, used in enumerate(self.used_tiles[letter]):
            if not used:
                return i
        return None
        
    def mark_tile_used(self, letter: str, index: int):
        letter = letter.upper()
        if letter in self.used_tiles and index < len(self.used_tiles[letter]):
            self.used_tiles[letter][index] = True
            
    def mark_tile_available(self, letter: str, index: int):
        letter = letter.upper()
        if letter in self.used_tiles and index < len(self.used_tiles[letter]):
            self.used_tiles[letter][index] = False
            
    def remove_last_typed(self):
        if self.typed_letters:
            letter, tile_index = self.typed_letters.pop()
            self.mark_tile_available(letter, tile_index)
            return letter
        return None
