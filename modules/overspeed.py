from modules.speed_limit_manager import (
    get_speed_limit
)

def check_overspeed(speed):

    limit = get_speed_limit()

    if speed > limit:

        return "OVERSPEED"

    return "NORMAL"