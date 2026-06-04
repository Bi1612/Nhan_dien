import cv2
import numpy as np

from config import *

from modules.bird_view import bird_to_camera

# ==========================================================
# Create Danger Zone
# ==========================================================

def create_danger_zone(speed_kmh):

    speed_ms = speed_kmh / 3.6

    S = speed_ms * 1.5

    pixels_per_meter = 20

    zone_height = int(
        S * pixels_per_meter
    )

    bird_zone = np.array([
        [160, 416-zone_height],
        [256, 416-zone_height],
        [256, 416],
        [160, 416]
    ])

    camera_zone = bird_to_camera(
        bird_zone
    )

    return camera_zone.astype(int)

# ==========================================================
# Draw Danger Zone
# ==========================================================

def draw_danger_zone(
    frame,
    zone
):

    cv2.polylines(
        frame,
        [zone],
        True,
        (0,0,255),
        3
    )

    overlay = frame.copy()

    cv2.fillPoly(
        overlay,
        [zone],
        (0,0,255)
    )

    cv2.addWeighted(
        overlay,
        0.20,
        frame,
        0.80,
        0,
        frame
    )