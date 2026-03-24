from service.screencast import ScreenCastCaptureLinux
from service.screencast import ScreenCastCaptureWindows
from core.matcher import MultiScaleTemplateMatcher
import cv2

# =============================================================================
# BOARD SCANNER
# =============================================================================

class BoardScanner:
    def __init__(self, PLATFORM, state=None, template_folder="templates", threshold=0.75):
        """Create a board scanner.

        Supports both call styles:
        - BoardScanner(state, ...)
        - BoardScanner(PLATFORM, state, ...)
        """
        if state is None:
            self.state = PLATFORM
        else:
            platform = PLATFORM
            self.state = state

        self.template_folder = template_folder
        self.threshold = threshold
        self.matcher = MultiScaleTemplateMatcher()
        
        if isinstance(platform, dict) and platform.get('system') == 'linux':
            print('Using ScreenCastCaptureLinux()')
            self.capture = ScreenCastCaptureLinux()
        else:
            print('Using ScreenCastCaptureWindows()')
            self.capture = ScreenCastCaptureWindows()
        
        self.last_screenshot = None
        self.last_detected = {}
        self.load_templates()

    def load_templates(self):
        print(f"Loading templates from: {self.template_folder}")
        count = self.matcher.load_templates(self.template_folder)
        print(f"Total templates loaded: {count}")
        return count
        
    def set_threshold(self, threshold):
        self.threshold = threshold
        
    def capture_board(self):
        if self.state.board_region is None:
            return None, "Board region not set"
        
        x, y, w, h = self.state.board_region
        
        if w < 10 or h < 10:
            return None, "Board region too small"

        screenshot = self.capture.capture_region(self.state.board_region)
        if screenshot is None:
            return None, "Failed to capture board (ScreenCast not ready?)"
            
        self.last_screenshot = screenshot
        return screenshot, None
        
    def scan_board(self):
        screenshot, error = self.capture_board()
        if screenshot is None:
            return None, {}, error
            
        detected = self.matcher.match(screenshot, self.threshold)
        self.last_detected = detected
        
        self.state.letter_positions = {}
        self.state.used_tiles = {}
        
        for letter, positions in detected.items():
            self.state.letter_positions[letter] = [(p[0], p[1]) for p in positions]
            self.state.used_tiles[letter] = [False] * len(positions)
            
        return screenshot, detected, None
        
    def get_annotated_screenshot(self, screenshot, detected):
        if screenshot is None: return None
        annotated = screenshot.copy()
        for letter, positions in detected.items():
            for pos in positions:
                x, y, w, h = pos
                top_left = (max(0, x - w // 2), max(0, y - h // 2))
                bottom_right = (x + w // 2, y + h // 2)
                cv2.rectangle(annotated, top_left, bottom_right, (0, 255, 0), 2)
                cv2.putText(annotated, letter, (top_left[0], top_left[1] - 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        return annotated