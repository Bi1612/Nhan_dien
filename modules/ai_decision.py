# ==========================================================
# File      : ai_decision.py
# Function  : Intelligent ADAS decision engine
# ==========================================================

def evaluate_ai_state(
    collision,
    lane,
    drowsiness,
    speed
):

    if collision == "DANGER":
        return "EMERGENCY"

    if drowsiness == "DROWSY":
        return "DRIVER FATIGUE"

    if lane == "LANE LOST":
        return "LANE WARNING"

    if speed == "OVERSPEED":
        return "SLOW DOWN"

    return "NORMAL"