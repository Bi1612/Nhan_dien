# ==========================================================
# File      : audio_alert.py
# Function  : ADAS audio warning system
# ==========================================================

import os

def play_alert(level):

    if level == "EMERGENCY":

        os.system(
            "aplay sounds/collision.wav &"
        )

    elif level == "LANE_WARNING":

        os.system(
            "aplay sounds/lane.wav &"
        )

    elif level == "OVERSPEED":

        os.system(
            "aplay sounds/overspeed.wav &"
        )