# ==================================================
# Blind Support Warning Controller (Refactored)
# ==================================================

def get_warning_level(fcw_status, lane_status=None, overspeed_status=None):
    if fcw_status == "DANGER":
        return "EMERGENCY"  # Vat can tinh chan loi (Bip lien tuc)
    if fcw_status == "WARNING":
        return "ALERT"      # Vat can dong o xa (Bip cham)
    return "NORMAL"
