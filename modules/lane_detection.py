import cv2
import numpy as np

def detect_lane_lines(frame):

    gray = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2GRAY
    )

    blur = cv2.GaussianBlur(
        gray,
        (5,5),
        0
    )

    edges = cv2.Canny(
        blur,
        50,
        150
    )

    lines = cv2.HoughLinesP(
        edges,
        1,
        np.pi/180,
        50,
        minLineLength=50,
        maxLineGap=30
    )

    return lines