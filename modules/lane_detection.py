import cv2
import numpy as np

def region_of_interest(img):

    height = img.shape[0]

    polygons = np.array([
        [
            (0, height),
            (416, height),
            (300, 250),
            (120, 250)
        ]
    ])

    mask = np.zeros_like(img)

    cv2.fillPoly(mask, polygons, 255)

    masked = cv2.bitwise_and(img, mask)

    return masked

def detect_lanes(frame):

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    edges = cv2.Canny(blur, 50, 150)

    cropped = region_of_interest(edges)

    lines = cv2.HoughLinesP(
        cropped,
        2,
        np.pi / 180,
        100,
        np.array([]),
        minLineLength=40,
        maxLineGap=5
    )

    return lines

def draw_lanes(frame, lines):

    if lines is None:
        return

    for line in lines:

        x1, y1, x2, y2 = line.reshape(4)

        cv2.line(
            frame,
            (x1, y1),
            (x2, y2),
            (0, 255, 0),
            5
        )