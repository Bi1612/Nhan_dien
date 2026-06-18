# ==================================================
# Blind Support Warning Controller (Refactored)
# ==================================================

def get_warning_level(
    fcw_status,
    lane_status=None,       # Thiết lập giá trị mặc định để tránh lỗi tương thích
    overspeed_status=None   # Lược bỏ các phân hệ ADAS cũ của ô tô
):
    """
    Trả về mức độ nguy hiểm để kích hoạt âm thanh / còi Buzzer cho người khiếm thị
    """
    if fcw_status == "DANGER":
        return "EMERGENCY"  # Vật cản cố định nằm chắn lối đi (Cần kêu bíp liên tục)

    if fcw_status == "WARNING":
        return "ALERT"      # Có vật thể chuyển động ở tầm xa (Bíp chậm)

    return "NORMAL"         # Trạng thái lối đi thông thoáng, an toàn
