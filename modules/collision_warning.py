from config import *

def estimate_distance(box_width):

    if box_width <= 0:
        return 999

    return (KNOWN_CAR_WIDTH * FOCAL_LENGTH) / box_width

def check_collision(distance):

    if distance < DANGER_DISTANCE:
        return "DANGER"

    elif distance < COLLISION_WARNING_DISTANCE:
        return "WARNING"

    return "SAFE"