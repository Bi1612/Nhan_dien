# ==========================================================
# File      : tracker.py
# Function  : Object tracking module
# ==========================================================

import cv2

tracker = None

tracking_initialized = False

# ==========================================================
# Initialize tracker
# ==========================================================

def init_tracker(frame, bbox):

    global tracker
    global tracking_initialized

    tracker = cv2.TrackerCSRT_create()

    tracker.init(frame, bbox)

    tracking_initialized = True

# ==========================================================
# Update tracker
# ==========================================================

def update_tracker(frame):

    global tracker
    global tracking_initialized

    if not tracking_initialized:
        return None

    success, box = tracker.update(frame)

    if success:
        return box

    tracking_initialized = False

    return None