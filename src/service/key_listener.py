from pynput import keyboard
from pynput.keyboard import Key, KeyCode

# =============================================================================
# INPUT LISTENER
# =============================================================================

class GlobalHotkeyListener:
    def __init__(self, on_hotkey_callback, on_type_callback):
        self.on_hotkey = on_hotkey_callback
        self.on_type = on_type_callback
        self.listener = None
        self.is_typing_active = False
        
    def start(self):
        if self.listener is None:
            self.listener = keyboard.Listener(on_press=self._on_press)
            self.listener.daemon = True
            self.listener.start()
            
    def set_typing_active(self, active):
        self.is_typing_active = active
        
    def _on_press(self, key):
        try:
            if key == Key.f9:
                self.on_hotkey("SCAN")
            elif key == Key.f10:
                self.on_hotkey("TOGGLE_LISTEN")
            elif key == Key.f8:
                self.on_hotkey("RESCAN")
                
            if self.is_typing_active:
                if isinstance(key, KeyCode) and key.char:
                    char = key.char.upper()
                    if char.isalpha() and len(char) == 1:
                        self.on_type("LETTER", char)
                elif isinstance(key, Key):
                    if key == Key.enter:
                        self.on_type("ATTACK", None)
                    elif key == Key.backspace:
                        self.on_type("DELETE", None)
                    elif key == Key.esc:
                        self.on_type("STOP", None)
        except Exception:
            pass