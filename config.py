FRAME_WIDTH = 416
FRAME_HEIGHT = 416

CONFIDENCE_THRESHOLD = 0.5

ADAS_CLASSES = [
    "person",
    "car",
    "motorcycle",
    "bus",
    "truck"
]

COLORS = {
    "person": (0, 0, 255),
    "car": (255, 0, 0),
    "motorcycle": (0, 255, 255),
    "bus": (0, 255, 0),
    "truck": (255, 0, 255)
}

KNOWN_CAR_WIDTH = 1.8
FOCAL_LENGTH = 700

COLLISION_WARNING_DISTANCE = 8
DANGER_DISTANCE = 4

# ==========================================================
# Speed Warning Configuration
# ==========================================================

MAX_SPEED_KMH = 40