# ==========================================================
# File      : audio_alert.py
# Function  : ADAS audio warning system
# ==========================================================

import os

# ==========================================================
# Play warning sound
# ==========================================================

def play_warning(message):

    os.system(
        f'espeak "{message}"'
    )