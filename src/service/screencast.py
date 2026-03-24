import threading
import dbus
import time
import numpy as np
import subprocess
import os
import cv2
import pyautogui

from PIL import ImageGrab
from typing import Optional, Tuple
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib, Gst

# =============================================================================
# SCREENCAST CAPTURE (Linux DBus + GStreamer)
# =============================================================================

class ScreenCastCaptureLinux:
    """
    Real-time screen capture using GNOME/Mutter ScreenCast API (PipeWire).
    Runs a GStreamer pipeline to consume the PipeWire stream.
    """

    def __init__(self):
        self.loop = None
        self.pipeline = None
        self.latest_frame = None
        self.frame_lock = threading.Lock()
        self.running = False
        self.session = None
        self.stream = None
        self.mainloop_thread = None
        
        # DBus interfaces
        self.screen_cast_iface = 'org.gnome.Mutter.ScreenCast'
        self.screen_cast_session_iface = 'org.gnome.Mutter.ScreenCast.Session'
        
        self.start()

    def start(self):
        """Initialize the ScreenCast session in a background thread."""
        if self.running:
            return

        print("Initializing ScreenCast...")
        self.mainloop_thread = threading.Thread(target=self._run_mainloop, daemon=True)
        self.mainloop_thread.start()
        
        # Wait a moment for initialization
        time.sleep(1.5)  # Slightly longer wait to ensure thread is ready

    def _run_mainloop(self):
        """Run the GLib MainLoop and setup DBus."""
        DBusGMainLoop(set_as_default=True)
        self.loop = GLib.MainLoop()
        
        try:
            bus = dbus.SessionBus()
            screen_cast_proxy = bus.get_object(self.screen_cast_iface, '/org/gnome/Mutter/ScreenCast')
            
            # Create Session
            session_path = screen_cast_proxy.CreateSession([], dbus_interface=self.screen_cast_iface)
            print(f"ScreenCast Session created: {session_path}")
            
            self.session = bus.get_object(self.screen_cast_iface, session_path)
            
            # Record Monitor 0 (Primary Monitor)
            stream_path = self.session.RecordMonitor(
                "", 
                dbus.types.Dictionary({'cursor-mode': dbus.UInt32(1, variant_level=1)}),
                dbus_interface=self.screen_cast_session_iface
            )
            print(f"Stream path: {stream_path}")
            
            self.stream = bus.get_object(self.screen_cast_iface, stream_path)
            self.stream.connect_to_signal("PipeWireStreamAdded", self._on_pipewire_stream_added)
            
            # Start the session
            self.session.Start(dbus_interface=self.screen_cast_session_iface)
            self.running = True
            
            print("ScreenCast Session Started. Waiting for stream...")
            self.loop.run()
            
        except Exception as e:
            print(f"Failed to initialize ScreenCast: {e}")
            print("Ensure you are running a Wayland compositor (GNOME/Mutter) and have permissions.")
            self.running = False

    def _on_pipewire_stream_added(self, node_id):
        """Callback when PipeWire stream is ready."""
        print(f"PipeWire Stream Added: node_id {node_id}")
        
        # GStreamer Pipeline:
        # 1. pipewiresrc: Get stream from PipeWire
        # 2. videoconvert: Convert format (handles BGRA->BGR automatically)
        # 3. caps filter: Force BGR format for OpenCV compatibility
        # 4. appsink: Capture frames in Python
        pipeline_str = (
            f"pipewiresrc path={node_id} ! "
            "videoconvert ! "
            "video/x-raw,format=BGR ! "
            "appsink name=sink emit-signals=True sync=False max-buffers=1 drop=True"
        )
        
        try:
            self.pipeline = Gst.parse_launch(pipeline_str)
            appsink = self.pipeline.get_by_name("sink")
            appsink.connect("new-sample", self._on_new_sample)
            
            # Add Bus Watcher to catch errors
            bus = self.pipeline.get_bus()
            bus.add_signal_watch()
            bus.connect("message::error", self._on_bus_error)
            bus.connect("message::warning", self._on_bus_warning)
            bus.connect("message::stream-status", self._on_bus_status)
            
            ret = self.pipeline.set_state(Gst.State.PLAYING)
            if ret == Gst.StateChangeReturn.FAILURE:
                print("ERROR: Pipeline failed to go to PLAYING state.")
                self.running = False
            else:
                print(f"GStreamer Pipeline playing (State: {ret}).")
            
        except Exception as e:
            print(f"Failed to start GStreamer pipeline: {e}")
            import traceback
            traceback.print_exc()

    def _on_bus_error(self, bus, message):
        """Handle GStreamer errors."""
        err, debug = message.parse_error()
        print(f"GStreamer ERROR: {err}")
        print(f"Debug Info: {debug}")
        self.running = False

    def _on_bus_warning(self, bus, message):
        """Handle GStreamer warnings."""
        warn, debug = message.parse_warning()
        print(f"GStreamer Warning: {warn}")

    def _on_bus_status(self, bus, message):
        """Handle stream status changes."""
        # Can be useful for debugging, but often noisy
        pass

    def _on_new_sample(self, sink):
        """GStreamer callback to process new frames."""
        sample = sink.emit("pull-sample")
        if sample:
            buffer = sample.get_buffer()
            caps = sample.get_caps()
            
            # Get frame dimensions
            structure = caps.get_structure(0)
            width = structure.get_value('width')
            height = structure.get_value('height')
            
            # Map buffer to readable memory
            result, map_info = buffer.map(Gst.MapFlags.READ)
            if result:
                try:
                    # Create numpy array
                    frame = np.frombuffer(map_info.data, dtype=np.uint8)
                    frame = frame.reshape((height, width, 3))
                    
                    with self.frame_lock:
                        self.latest_frame = frame.copy()
                        
                except Exception as e:
                    print(f"Frame processing error: {e}")
                finally:
                    buffer.unmap(map_info)
                    
            return Gst.FlowReturn.OK
        return Gst.FlowReturn.ERROR

    def capture_region(self, region):
        """Capture a specific region from the latest frame."""
        with self.frame_lock:
            if self.latest_frame is None:
                return None
            full_frame = self.latest_frame.copy()
        
        x, y, w, h = region
        
        # Crop region with safety checks
        frame_h, frame_w = full_frame.shape[:2]
        
        x1, y1 = max(0, x), max(0, y)
        x2, y2 = min(frame_w, x + w), min(frame_h, y + h)
        
        if x2 <= x1 or y2 <= y1:
            return None
            
        return full_frame[y1:y2, x1:x2]

    def capture_full(self):
        """Capture full screen."""
        with self.frame_lock:
            return self.latest_frame.copy() if self.latest_frame is not None else None

    def stop(self):
        """Stop the pipeline and session."""
        if self.pipeline:
            self.pipeline.send_event(Gst.Event.new_eos())
            self.pipeline.set_state(Gst.State.NULL)
        if self.loop:
            self.loop.quit()
        self.running = False

# =============================================================================
# SCREEN CAPTURE (Windows)
# =============================================================================

class ScreenCastCaptureWindows:
    """
    Screen capture with Opevcv + PIL ImageGrab.
    """
                
    def capture_region(self, region):
        """Capture a specific region of the screen."""
        x, y, w, h = region
        
        if w < 10 or h < 10:
            return None
            
        # Try PIL ImageGrab first (works on most systems)
        try:
            img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
            if img is not None:
                return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        except Exception as e:
            print(f"ImageGrab failed: {e}")
            
        # Try scrot on Linux
        if self.use_scrot and self.scrot_path:
            try:
                import tempfile
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                    tmp_path = tmp.name
                    
                subprocess.run([
                    'scrot', '-a', f'{x},{y},{w},{h}', tmp_path
                ], check=True, timeout=5, capture_output=True)
                
                if os.path.exists(tmp_path):
                    img = cv2.imread(tmp_path)
                    os.unlink(tmp_path)
                    if img is not None:
                        return img
            except Exception as e:
                print(f"scrot failed: {e}")
                
        # Try pyautogui as last resort
        try:
            screenshot = pyautogui.screenshot(region=(x, y, w, h))
            return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        except Exception as e:
            print(f"pyautogui failed: {e}")
            
        return None
        
    def capture_full(self) -> Optional[np.ndarray]:
        """Capture full screen."""
        try:
            img = ImageGrab.grab()
            if img is not None:
                return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        except Exception as e:
            print(f"Full capture failed: {e}")
            
        return None