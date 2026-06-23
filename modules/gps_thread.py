import threading
import modules.shared_data as shared

class GPSThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True  # Giúp luồng tự giải phóng hoàn toàn khi tắt app chính

    def run(self):
        # Ép nạp cục bộ thư viện time để tránh xung đột môi trường nhúng trên Jetson
        import time 
        
        print("[INFO] Luong GPS gia lap da duoc kich hoat an toan.")
        
        # Khởi tạo giá trị ban đầu để app_final không bị lỗi gạt dữ liệu
        shared.latitude = 21.0065   # Tọa độ mặc định khu vực Bách Khoa HUST
        shared.longitude = 105.8429
        shared.gps_speed = 5.0      # Vận tốc đi bộ mặc định (km/h)
        shared.gps_valid = True     # Đánh dấu dữ liệu GPS hợp lệ
        
        fake_direction = 1          # Biến phụ để làm vận tốc biến thiên cho sinh động
        
        while shared.running:
            try:
                # Giữ tọa độ cố định tại trường để cô Thảo check thuật toán không gian
                shared.latitude = 21.0065  
                shared.longitude = 105.8429
                shared.gps_valid = True
                
                # Giả lập vận tốc đi bộ thực tế dao động từ 4.0 đến 6.0 km/h
                shared.gps_speed += 0.2 * fake_direction
                if shared.gps_speed > 6.0:
                    fake_direction = -1
                elif shared.gps_speed < 4.0:
                    fake_direction = 1
                    
            except Exception as e:
                print(f"[WARNING] Loi cap nhat du lieu GPS: {e}")
                shared.gps_valid = False
            
            # Nghỉ 1 giây mỗi chu kỳ để bảo vệ tài nguyên CPU, chống đơ lag máy
            time.sleep(1.0)

    # === HÀM FIX LỖI CỦA BI ===
    def stop(self):
        pass
