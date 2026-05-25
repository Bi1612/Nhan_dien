# ==========================================================
# File      : shared_data.py
# Function  : Shared memory between ADAS threads
# ==========================================================

frame = None

detections = []

lines = None

sign_type = None
sign_box = None

gps_speed = 0.0

running = True

sensor_distance = 999.0

ax = 0
ay = 0
az = 0