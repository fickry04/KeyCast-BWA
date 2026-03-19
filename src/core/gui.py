import tkinter as tk
import cv2
import time

from PIL import Image, ImageTk
from config.config import AppConfig, AppState
from service.scanner import BoardScanner
from service.key_listener import GlobalHotkeyListener
from controller.click_controller import ClickController
from core.region_selector import RegionSelector
from tkinter import scrolledtext


# =============================================================================
# MAIN GUI
# =============================================================================

class AppGUI:
    def __init__(self):
        self.config = AppConfig()
        self.state = AppState(self.config)
        
        self.root = tk.Tk()
        self.root.title("Bookworm Adventure KeyCast")
        self.root.geometry("1000x850")
        self.root.configure(bg='#1e1e1e')
        
        self.scanner = BoardScanner(self.state, template_folder="templates", threshold=self.config.config['threshold'])
        self.click_controller = ClickController(self.state)
        
        self.hotkey_listener = GlobalHotkeyListener(self.handle_global_hotkey, self.handle_typing_input)
        self.hotkey_listener.start()
        
        self.preview_image = None
        self.is_auto_rescan = tk.BooleanVar(value=self.config.config['auto_rescan'])
        self.rescan_delay = tk.DoubleVar(value=self.config.config['rescan_delay'])
        
        self.create_widgets()
        self.center_window()
        self.load_saved_config()
        
    def center_window(self):
        self.root.update_idletasks()
        w, h = self.root.winfo_width(), self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f'{w}x{h}+{x}+{y}')
        
    def load_saved_config(self):
        if self.state.board_region:
            x, y, w, h = self.state.board_region
            self.board_label.config(text=f"Board: OK ({w}x{h})", fg='#4ecdc4')
        if self.state.attack_button_position:
            x, y = self.state.attack_button_position
            self.attack_label.config(text=f"Attack: OK ({x},{y})", fg='#4ecdc4')
        if self.state.delete_button_position:
            x, y = self.state.delete_button_position
            self.delete_label.config(text=f"Delete: OK ({x},{y})", fg='#4ecdc4')
            
    def create_widgets(self):
        main_frame = tk.Frame(self.root, bg='#1e1e1e')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Header
        header_frame = tk.Frame(main_frame, bg='#1e1e1e')
        header_frame.pack(fill=tk.X, pady=(0, 5))
        
        tk.Label(header_frame, text="Bookworm Adventures Vol. 2 Trainer", font=('Sans', 18, 'bold'), bg='#1e1e1e', fg='#4ecdc4').pack(side=tk.LEFT)
        
        self.status_indicator = tk.Label(header_frame, text="STOPPED", font=('Sans', 12, 'bold'), bg='#1e1e1e', fg='#ff6b6b')
        self.status_indicator.pack(side=tk.RIGHT)
        
        # Info
        info_frame = tk.Frame(main_frame, bg='#252526', padx=10, pady=8)
        info_frame.pack(fill=tk.X, pady=(0, 5))
        tk.Label(info_frame, text="GLOBAL HOTKEYS: [F9] Scan Board | [F10] Start/Stop | [F8] Force Rescan", bg='#252526', fg='#ffcc00', font=('Sans', 10, 'bold')).pack(fill=tk.X)
        tk.Label(info_frame, text="During listening: [A-Z] Type letters | [Enter] Attack | [Backspace] Delete | [Esc] Stop", bg='#252526', fg='#aaaaaa', font=('Sans', 9)).pack(fill=tk.X)
        
        # Config
        config_frame = tk.LabelFrame(main_frame, text="Configuration", font=('Sans', 11, 'bold'), bg='#2d2d2d', fg='#ffffff', padx=10, pady=10)
        config_frame.pack(fill=tk.X, pady=(0, 10))
        
        btn_frame = tk.Frame(config_frame, bg='#2d2d2d')
        btn_frame.pack(fill=tk.X, pady=5)
        
        btn_style = {'font': ('Sans', 10), 'bg': '#3d3d3d', 'fg': '#ffffff', 'relief': tk.FLAT, 'padx': 15, 'pady': 8}
        
        tk.Button(btn_frame, text="Select Board Area", command=lambda: self.select_area('board'), **btn_style).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Select Attack Button", command=lambda: self.select_area('attack'), **btn_style).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Select Delete Button", command=lambda: self.select_area('delete'), **btn_style).pack(side=tk.LEFT, padx=5)
        
        status_frame = tk.Frame(config_frame, bg='#2d2d2d')
        status_frame.pack(fill=tk.X, pady=5)
        
        self.board_label = tk.Label(status_frame, text="Board: Not Set", font=('Monospace', 9), bg='#2d2d2d', fg='#666666')
        self.board_label.pack(side=tk.LEFT, padx=10)
        
        self.attack_label = tk.Label(status_frame, text="Attack: Not Set", font=('Monospace', 9), bg='#2d2d2d', fg='#666666')
        self.attack_label.pack(side=tk.LEFT, padx=10)
        
        self.delete_label = tk.Label(status_frame, text="Delete: Not Set", font=('Monospace', 9), bg='#2d2d2d', fg='#666666')
        self.delete_label.pack(side=tk.LEFT, padx=10)
        
        # Controls
        control_frame = tk.LabelFrame(main_frame, text="Controls", font=('Sans', 11, 'bold'), bg='#2d2d2d', fg='#ffffff', padx=10, pady=10)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        ctrl_btn_frame = tk.Frame(control_frame, bg='#2d2d2d')
        ctrl_btn_frame.pack(fill=tk.X, pady=5)
        
        self.btn_scan = tk.Button(ctrl_btn_frame, text="Scan Board (F9)", command=self.scan_board, bg='#4a9eff', fg='#ffffff', font=('Sans', 10, 'bold'), relief=tk.FLAT, padx=20, pady=8)
        self.btn_scan.pack(side=tk.LEFT, padx=5)
        
        self.btn_start = tk.Button(ctrl_btn_frame, text="Start Listening (F10)", command=self.toggle_listening, bg='#4ecdc4', fg='#ffffff', font=('Sans', 10, 'bold'), relief=tk.FLAT, padx=20, pady=8)
        self.btn_start.pack(side=tk.LEFT, padx=5)
        
        threshold_frame = tk.Frame(ctrl_btn_frame, bg='#2d2d2d')
        threshold_frame.pack(side=tk.RIGHT, padx=10)
        tk.Label(threshold_frame, text="Threshold:", font=('Sans', 9), bg='#2d2d2d', fg='#aaaaaa').pack(side=tk.LEFT)
        
        self.threshold_var = tk.DoubleVar(value=self.config.config['threshold'])
        tk.Scale(threshold_frame, from_=0.5, to=0.95, resolution=0.05, orient=tk.HORIZONTAL, variable=self.threshold_var, command=self.update_threshold, length=120, bg='#2d2d2d', fg='#ffffff', troughcolor='#3d3d3d').pack(side=tk.LEFT)
        
        auto_frame = tk.Frame(control_frame, bg='#2d2d2d')
        auto_frame.pack(fill=tk.X, pady=5)
        tk.Checkbutton(auto_frame, text="Auto-rescan after attack", variable=self.is_auto_rescan, bg='#2d2d2d', fg='#aaaaaa', selectcolor='#3d3d3d', font=('Sans', 9)).pack(side=tk.LEFT, padx=5)
        
        # Preview
        preview_frame = tk.LabelFrame(main_frame, text="Board Preview", font=('Sans', 11, 'bold'), bg='#2d2d2d', fg='#ffffff', padx=10, pady=10)
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.preview_canvas = tk.Canvas(preview_frame, bg='#1a1a1a', highlightthickness=0)
        self.preview_canvas.pack(fill=tk.BOTH, expand=True)
        self.preview_canvas.create_text(400, 100, text="Waiting for ScreenCast stream...", font=('Sans', 14), fill='#555555', tags='placeholder')
        
        # Letters
        letter_frame = tk.LabelFrame(main_frame, text="Detected Letters", font=('Sans', 11, 'bold'), bg='#2d2d2d', fg='#ffffff', padx=10, pady=10)
        letter_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.letter_display = tk.Label(letter_frame, text="No letters detected", font=('Monospace', 11), bg='#2d2d2d', fg='#4ecdc4', wraplength=900, justify=tk.LEFT)
        self.letter_display.pack(fill=tk.X)
        
        # Log
        log_frame = tk.LabelFrame(main_frame, text="Activity Log", font=('Sans', 11, 'bold'), bg='#2d2d2d', fg='#ffffff', padx=10, pady=10)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=5, bg='#0d0d0d', fg='#4ecdc4', font=('Monospace', 9), relief=tk.FLAT)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        self.log("=" * 60)
        self.log("Bookworm Trainer Ready - Linux ScreenCast Edition")
        self.log("=" * 60)
        self.log("ScreenCast API active. Waiting for configuration.")
        
    def log(self, message):
        self.log_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {message}\n")
        self.log_text.see(tk.END)
        
    def update_threshold(self, val):
        self.scanner.set_threshold(float(val))
        self.config.config['threshold'] = float(val)
        self.config.save()
        
    def select_area(self, target):
        self.log(f"Selecting area for {target}...")
        if target == 'board':
            RegionSelector(self.root, lambda r: self.set_region('board', r), mode='area')
        elif target == 'attack':
            RegionSelector(self.root, lambda r: self.set_region('attack', r), mode='point')
        elif target == 'delete':
            RegionSelector(self.root, lambda r: self.set_region('delete', r), mode='point')
            
    def set_region(self, target, data):
        if not data:
            self.log("Selection cancelled")
            return
            
        if target == 'board':
            x, y, w, h = data
            self.state.board_region = data
            self.board_label.config(text=f"Board: OK ({w}x{h})", fg='#4ecdc4')
            self.log(f"Board area set: ({x},{y}) {w}x{h}")
        elif target == 'attack':
            x, y = data
            self.state.attack_button_position = data
            self.attack_label.config(text=f"Attack: OK ({x},{y})", fg='#4ecdc4')
            self.log(f"Attack button set: ({x},{y})")
        elif target == 'delete':
            x, y = data
            self.state.delete_button_position = data
            self.delete_label.config(text=f"Delete: OK ({x},{y})", fg='#4ecdc4')
            self.log(f"Delete button set: ({x},{y})")
            
        self.state.save_to_config()
        
    def scan_board(self):
        if self.state.board_region is None:
            self.log("ERROR: Set Board Area first!")
            return
            
        self.log("Scanning board...")
        
        screenshot, detected, error = self.scanner.scan_board()
        
        if error:
            self.log(f"ERROR: {error}")
            return
            
        if screenshot is None:
            self.log("ERROR: No frame available from ScreenCast.")
            return
            
        annotated = self.scanner.get_annotated_screenshot(screenshot, detected)
        self.display_preview(annotated)
        self.update_letter_display(detected)
        
        total = sum(len(p) for p in detected.values())
        if total > 0:
            summary = " ".join(f"{l}:{len(p)}" for l, p in sorted(detected.items()))
            self.log(f"Detected {total} letters: {summary}")
        else:
            self.log("No letters detected.")
            
    def update_letter_display(self, detected):
        if not detected:
            self.letter_display.config(text="No letters detected")
            return
            
        parts = []
        for letter in sorted(detected.keys()):
            count = len(detected[letter])
            available = self.state.used_tiles.get(letter, [])
            avail_count = sum(1 for u in available if not u)
            parts.append(f"{letter}:{avail_count}/{count}")
        self.letter_display.config(text=" | ".join(parts))
        
    def toggle_listening(self):
        current = self.hotkey_listener.is_typing_active
        self.hotkey_listener.set_typing_active(not current)
        
        if not current:
            if not self.state.letter_positions:
                self.log("ERROR: Scan board first (F9)!")
                self.hotkey_listener.set_typing_active(False)
                return
            self.status_indicator.config(text="RUNNING", fg='#4ecdc4')
            self.btn_start.config(text="Stop Listening (F10)", bg='#ff6b6b')
            self.log("Listening STARTED")
        else:
            self.status_indicator.config(text="STOPPED", fg='#ff6b6b')
            self.btn_start.config(text="Start Listening (F10)", bg='#4ecdc4')
            self.log("Listening STOPPED")
            
    def handle_global_hotkey(self, action):
        if action == "SCAN":
            self.root.after(0, self.scan_board)
        elif action == "TOGGLE_LISTEN":
            self.root.after(0, self.toggle_listening)
        elif action == "RESCAN":
            self.root.after(0, self.force_rescan)
            
    def handle_typing_input(self, action, data):
        if action == "LETTER":
            success, msg = self.click_controller.click_letter(data)
            self.root.after(0, lambda: self.log(f"Key: {data} -> {msg}"))
            self.root.after(0, lambda: self.update_letter_display(self.scanner.last_detected))
        elif action == "ATTACK":
            success, msg = self.click_controller.click_attack()
            self.root.after(0, lambda: self.log(f"Key: ENTER -> Attack"))
            self.state.reset_tiles()
            if self.is_auto_rescan.get():
                delay = self.rescan_delay.get()
                self.root.after(int(delay * 1000), self.scan_board)
        elif action == "DELETE":
            self.click_controller.click_delete()
            self.state.reset_tiles()
            self.root.after(0, lambda: self.log("Key: BACKSPACE -> reset all tiles"))
            self.root.after(0, lambda: self.update_letter_display(self.scanner.last_detected))
        elif action == "STOP":
            self.root.after(0, self.toggle_listening)
            
    def force_rescan(self):
        self.state.reset_tiles()
        self.scan_board()
        
    def display_preview(self, cv_image):
        if cv_image is None: return
        self.preview_canvas.delete('placeholder')
        
        canvas_w = self.preview_canvas.winfo_width()
        canvas_h = self.preview_canvas.winfo_height()
        if canvas_w < 50: canvas_w = 900
        if canvas_h < 50: canvas_h = 200
        
        h, w = cv_image.shape[:2]
        scale = min(canvas_w / w, canvas_h / h, 1.0)
        new_w, new_h = int(w * scale), int(h * scale)
        
        resized = cv2.resize(cv_image, (new_w, new_h))
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb)
        self.preview_image = ImageTk.PhotoImage(pil_image)
        
        self.preview_canvas.delete("all")
        self.preview_canvas.create_image(canvas_w // 2, canvas_h // 2, image=self.preview_image, anchor=tk.CENTER)
        
    def run(self):
        self.root.mainloop()