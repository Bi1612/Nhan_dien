# ==========================================================
# File      : lane_thread.py
# Function  : Lane detection thread
# ==========================================================

import threading
import time

import modules.shared_data as shared

from modules.lane_detection import detect_lanes

# ==========================================================
# Lane detection thread
# ==========================================================

class LaneThread(threading.Thread):

    def __init__(self):

        threading.Thread.__init__(self)

        self.daemon = True

    # ======================================================
    # Main lane detection loop
    # ======================================================

    def run(self):

        while shared.running:

            if shared.frame is not None:

                lines = detect_lanes(shared.frame)

                shared.lines = lines

            time.sleep(0.001)