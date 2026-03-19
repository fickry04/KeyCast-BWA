import pyautogui
import os
import sys

from gi.repository import Gst
from core.gui import AppGUI

# Configuration
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.01

# Initialize GStreamer
Gst.init(None)

# =============================================================================
# PLATFORM DETECTION
# =============================================================================

def get_platform():
    """Detect the current platform."""
    if sys.platform == 'linux':
        wayland = os.environ.get('WAYLAND_DISPLAY') is not None
        x11 = os.environ.get('DISPLAY') is not None
        return {
            'system': 'linux',
            'wayland': wayland,
            'x11': x11
        }
    elif sys.platform == 'win32':
        return {'system': 'windows'}
    elif sys.platform == 'darwin':
        return {'system': 'mac'}
    return {'system': 'unknown'}

PLATFORM = get_platform()

# =============================================================================
# MAIN
# =============================================================================

def create_templates_folder():
    if not os.path.exists("templates"):
        os.makedirs("templates")
        print("Created 'templates' folder. Please add letter images (A.png, B.png, ...) Or use template_creator.py")

def main():
    print("=" * 60)
    print("Bookworm Adventures KeyCast")
    print("=" * 60)
    create_templates_folder()
    app = AppGUI()
    app.run()

if __name__ == "__main__":
    main()