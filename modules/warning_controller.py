# ==================================================
# ADAS Warning Controller
# ==================================================

def get_warning_level(
    fcw_status,
    lane_status,
    overspeed_status
):

    if fcw_status == "DANGER":

        return "EMERGENCY"

    if lane_status != "CENTER":

        return "LANE_WARNING"

    if overspeed_status == "OVERSPEED":

        return "OVERSPEED"

    return "NORMAL"