# ==========================================================
# File      : speed_warning.py
# Function  : Overspeed warning logic
# ==========================================================

from config import MAX_SPEED_KMH

# ==========================================================
# Function : check_speed
# Purpose  : Check if vehicle exceeds speed limit
# Input    : speed_kmh
# Output   : SAFE / OVERSPEED
# ==========================================================

def check_speed(speed_kmh):

    if speed_kmh > MAX_SPEED_KMH:
        return "OVERSPEED"

    return "SAFE"