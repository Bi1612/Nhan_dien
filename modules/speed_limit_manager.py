import time

current_speed_limit = 50

last_sign_time = 0

SIGN_MEMORY_TIME = 1800


def update_speed_limit(limit):

    global current_speed_limit
    global last_sign_time

    current_speed_limit = limit

    last_sign_time = time.time()


def get_speed_limit():

    global current_speed_limit
    global last_sign_time

    if time.time() - last_sign_time > SIGN_MEMORY_TIME:

        current_speed_limit = 50

    return current_speed_limit