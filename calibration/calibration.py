import cv2
import json
import numpy as np

CONFIG_FILE = "calibration/calibration.json"

def load_calibration():

    with open(CONFIG_FILE, "r") as f:

        data = json.load(f)

    src = np.float32(
        data["src_points"]
    )

    dst = np.float32(
        data["dst_points"]
    )

    H = cv2.getPerspectiveTransform(
        src,
        dst
    )

    Hinv = cv2.getPerspectiveTransform(
        dst,
        src
    )

    pixel_per_meter = data[
        "pixel_per_meter"
    ]

    return (
        H,
        Hinv,
        pixel_per_meter
    )