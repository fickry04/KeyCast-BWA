import tkinter as tk
import time

# =============================================================================
# REGION SELECTOR (Linux Compatible)
# =============================================================================

class RegionSelector:
    def __init__(self, parent, callback, mode='area'):
        self.parent = parent
        self.callback = callback
        self.mode = mode
        self.start_x = None
        self.start_y = None
        self.current_rect = None
        self.selection_made = False
        
        if parent:
            parent.withdraw()
            
        time.sleep(0.15)
        
        self.window = tk.Toplevel()
        self.window.attributes('-fullscreen', True)
        self.window.attributes('-topmost', True)
        
        try:
            self.window.attributes('-alpha', 0.3)
        except tk.TclError:
            pass
            
        self.window.configure(bg='#000000', cursor='crosshair')
        
        self.canvas = tk.Canvas(self.window, bg='#000000', highlightthickness=0, cursor='crosshair')
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        self.canvas.bind('<Button-1>', self.on_mouse_down)
        self.canvas.bind('<B1-Motion>', self.on_mouse_move)
        self.canvas.bind('<ButtonRelease-1>', self.on_mouse_up)
        self.window.bind('<Escape>', self.cancel)
        self.window.bind('<Button-3>', self.cancel)
        
        self.window.after(50, self.draw_instructions)
        
    def draw_instructions(self):
        sw = self.window.winfo_screenwidth()
        sh = self.window.winfo_screenheight()
        
        text = "DRAG to select area" if self.mode == 'area' else "CLICK to select point"
        text += " (ESC to cancel)"
        
        self.canvas.create_rectangle(0, 0, sw, 50, fill='#333333', outline='')
        self.canvas.create_text(sw // 2, 25, text=text, fill='#00ff00', font=('Sans', 14, 'bold'))
        
    def on_mouse_down(self, event):
        self.start_x = event.x
        self.start_y = event.y
        
        if self.mode == 'point':
            self.selection_made = True
            self.window.destroy()
            if self.parent: self.parent.deiconify()
            self.callback((event.x_root, event.y_root))
            
    def on_mouse_move(self, event):
        if self.mode == 'area' and self.start_x is not None:
            if self.current_rect: self.canvas.delete(self.current_rect)
            self.current_rect = self.canvas.create_rectangle(
                self.start_x, self.start_y, event.x, event.y,
                outline='#00ff00', width=3, fill=''
            )
            
    def on_mouse_up(self, event):
        if self.mode == 'area' and self.start_x is not None:
            x1, y1 = self.start_x, self.start_y
            x2, y2 = event.x_root, event.y_root
            
            x, y = min(x1, x2), min(y1, y2)
            w, h = abs(x2 - x1), abs(y2 - y1)
            
            self.selection_made = True
            self.window.destroy()
            if self.parent: self.parent.deiconify()
            
            if w > 20 and h > 20:
                self.callback((x, y, w, h))
            else:
                self.callback(None)
                
    def cancel(self, event=None):
        if not self.selection_made:
            self.window.destroy()
            if self.parent: self.parent.deiconify()
            self.callback(None)