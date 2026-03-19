import pyautogui
import time

# =============================================================================
# CLICK CONTROLLER
# =============================================================================

class ClickController:
    def __init__(self, state):
        self.state = state
        self.click_delay = 0.05
        
    def click_letter(self, letter):
        letter = letter.upper()
        if letter not in self.state.letter_positions:
            return False, f"Letter '{letter}' not found"
            
        tile_index = self.state.get_available_tile(letter)
        if tile_index is None:
            return False, f"No available tile for '{letter}'"
            
        rel_x, rel_y = self.state.letter_positions[letter][tile_index]
        
        if self.state.board_region:
            abs_x = self.state.board_region[0] + rel_x
            abs_y = self.state.board_region[1] + rel_y
        else:
            abs_x, abs_y = rel_x, rel_y
            
        try:
            pyautogui.click(abs_x, abs_y)
            time.sleep(self.click_delay)
            self.state.mark_tile_used(letter, tile_index)
            self.state.typed_letters.append((letter, tile_index))
            return True, f"click ({abs_x},{abs_y})"
        except Exception as e:
            return False, str(e)
            
    def click_attack(self):
        if self.state.attack_button_position is None:
            return False, "Attack button not set"
        x, y = self.state.attack_button_position
        try:
            pyautogui.click(x, y)
            return True, "Attack clicked"
        except Exception as e:
            return False, str(e)
            
    def click_delete(self):
        if self.state.delete_button_position is None:
            return False, "Delete button not set"
        x, y = self.state.delete_button_position
        try:
            pyautogui.click(x, y)
            return True, "Delete clicked"
        except Exception as e:
            return False, str(e)