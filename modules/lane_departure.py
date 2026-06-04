from config import *

def check_lane_departure(
    left_x,
    right_x,
    frame_width
):

    center = frame_width / 2

    AC = abs(
        center - left_x
    ) / center

    BC = abs(
        right_x - center
    ) / center

    if (
        AC < LANE_D1
        and
        BC > LANE_D2
    ):
        return "LEFT"

    if (
        AC > LANE_D2
        and
        BC < LANE_D1
    ):
        return "RIGHT"

    return "CENTER"