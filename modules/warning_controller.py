# ==============================================================================
# BLIND SUPPORT WARNING CONTROLLER (REFACTORED)
# ==============================================================================

def get_warning_level(fcw_status, lane_status=None, overspeed_status=None):
    """
    Bộ điều khiển trung tâm ra quyết định trạng thái còi Buzzer cho người khiếm thị
    """
    if fcw_status == "DANGER":
        return "EMERGENCY"  # Vật cản cố định (Còi kêu bíp liên tục, dồn dập)

    if fcw_status == "WARNING":
        return "ALERT"      # Vật cản động hoặc ở khoảng cách xa (Còi bíp chậm ngắt quãng)

    return "NORMAL"         # Đường đi thông thoáng, an toàn
