import threading
import serial
import modules.shared_data as shared

class SensorThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True

    def run(self):
        # KHẮC PHỤC TRIỆT ĐỂ: Ép nạp cục bộ thư viện time ngay tại đây
        import time 
        
        # Đoạn này tùy thuộc vào cấu hình cổng Serial trên mạch Jetson của bạn
        try:
            ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
        except Exception as e:
            print(f"[WARNING] Khong ket noi duoc cong Serial: {e}")
            ser = None

        while shared.running:
            if ser and ser.in_waiting > 0:
                try:
                    # Đọc dữ liệu khoảng cách siêu âm hoặc trạng thái nút bấm thủ công
                    line = ser.readline().decode('utf-8').strip()
                    if line.isdigit():
                        shared.distance = float(line)
                except Exception:
                    pass
            
            # Sử dụng time an toàn không lo import chéo
            time.sleep(0.05)
