import time

last_change = 0

current_sign = "NONE"


def detect_traffic_sign(frame):

    global last_change
    global current_sign

    if time.time() - last_change > 10:

        current_sign = "SPEED_30"

        last_change = time.time()

    return current_sign