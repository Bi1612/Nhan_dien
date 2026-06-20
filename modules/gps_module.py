import threading
import modules.shared_data as shared

class GPSThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True

    def run(self):
        # KHẮC PHỤC TRIỆT ĐỂ: Ép nạp cục bộ thư viện time ngay tại đây
        import time 
        
        print("[INFO] Luong GPS da duoc kich hoat an toan.")
        
        while shared.running:
            try:
                # Đoạn này giả lập hoặc đọc dữ liệu tọa độ GPS thực tế từ module phần cứng
                # Hiện tại giữ luồng chạy ngầm ổn định để không làm treo mạch của cô
                shared.gps_lat = 21.0065  # Tọa độ giả lập khu vực Bách Khoa
                shared.gps_lon = 105.8429
            except Exception as e:
                print(f"[WARNING] Loi doc du lieu GPS: {e}")
            
            # Nghỉ 1 giây mỗi lần cập nhật tọa độ để tránh quá nhiệt mạch nhúng
            time.sleep(1.0)