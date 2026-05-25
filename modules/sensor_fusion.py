# ==========================================================
# File      : sensor_fusion.py
# Function  : ADAS sensor fusion engine
# ==========================================================

# ==========================================================
# Fusion collision risk
# ==========================================================

def evaluate_risk(
    distance,
    speed,
    acceleration
):

    if distance < 30 and speed > 40:
        return "DANGER"

    if distance < 60 and speed > 20:
        return "WARNING"

    return "SAFE"