import cv2

from config import *

# ==========================================================
# Point in Polygon
# ==========================================================

def point_inside_zone(
    point,
    zone
):

    result = cv2.pointPolygonTest(
        zone,
        point,
        False
    )

    return result >= 0

# ==========================================================
# FCW
# ==========================================================

def check_forward_collision(
    detections,
    zone,
    speed_kmh,
    distance
):

    if speed_kmh < FCW_ENABLE_SPEED:

        return "SAFE"

    for obj in detections:

        cls = obj["class"]

        if cls not in [
            "person",
            "car",
            "truck",
            "bus",
            "motorcycle"
        ]:
            continue

        x1,y1,x2,y2 = map(
            int,
            obj["box"]
        )

        bottom_center = (
            int((x1+x2)/2),
            y2
        )

        inside = point_inside_zone(
            bottom_center,
            zone
        )

        if inside:

            if distance < 150:

                return "DANGER"

            return "WARNING"

    return "SAFE"