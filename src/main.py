import pyautogui
import os
import sys

from core.gui import AppGUI

# Configuration
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.01

def _init_gstreamer_if_available() -> None:
    """Initialize GStreamer on Linux only.

    Windows builds should not require PyGObject/GStreamer at import time.
    """
    if sys.platform != "linux":
        return

    try:
        import gi  # type: ignore
        gi.require_version("Gst", "1.0")
        from gi.repository import Gst  # type: ignore
    except Exception as exc:
        raise RuntimeError(
            "GStreamer (PyGObject) is required on Linux for ScreenCast capture. "
            "Install system GStreamer + PyGObject packages, then retry."
        ) from exc

    Gst.init(None)

_init_gstreamer_if_available()

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
    elif sys.platform == 'win32' or sys.platform == 'win64':
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
    app = AppGUI(PLATFORM)
    app.run()

if __name__ == "__main__":
    main()