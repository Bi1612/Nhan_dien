# ==========================================================
# File      : traffic_sign.py
# Function  : Traffic sign recognition module
# Author    : Your Name
# Target    : NVIDIA Jetson Nano
# ==========================================================

import cv2
import numpy as np

# ==========================================================
# Function : detect_traffic_sign
# Purpose  : Detect red traffic signs
# Input    : frame
# Output   : sign_type, bounding box
# Notes    : Basic color segmentation approach
# ==========================================================

def detect_traffic_sign(frame):

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Red color range
    lower_red1 = np.array([0, 120, 70])
    upper_red1 = np.array([10, 255, 255])

    lower_red2 = np.array([170, 120, 70])
    upper_red2 = np.array([180, 255, 255])

    mask1 = cv2.inRange(
        hsv,
        lower_red1,
        upper_red1
    )

    mask2 = cv2.inRange(
        hsv,
        lower_red2,
        upper_red2
    )

    mask = mask1 + mask2

    contours, _ = cv2.findContours(
        mask,
        cv2.RETR_TREE,
        cv2.CHAIN_APPROX_SIMPLE
    )

    for cnt in contours:

        area = cv2.contourArea(cnt)

        if area > 500:

            x, y, w, h = cv2.boundingRect(cnt)

            aspect_ratio = w / float(h)

            # Approximate circular sign
            if 0.8 < aspect_ratio < 1.2:

                return "TRAFFIC SIGN", (x, y, w, h)

    return None, None