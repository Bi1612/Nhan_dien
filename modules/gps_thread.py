import threading
import serial
import pynmea2
import modules.shared_data as shared

class GPSThread(threading.Thread):
    def __init__(self, port='/dev/ttyUSB0', baudrate=9600):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.daemon = True  # Tự động giải phóng luồng khi tắt app chính

    def run(self):
        import time # Ép nạp cục bộ chống xung đột môi trường nhúng
        print(f"[GPS REAL] Đang kết nối cổng phần cứng {self.port} với Baudrate {self.baudrate}...")
        
        # Khởi tạo giá trị nền ban đầu
        shared.latitude = 0.0
        shared.longitude = 0.0
        shared.gps_speed = 0.0
        shared.gps_valid = False  # Mặc định ban đầu báo chưa có sóng vệ tinh
        
        try:
            # Mở cổng kết nối Serial vật lý với mạch chuyển đổi USB-to-TTL của GPS
            ser = serial.Serial(self.port, baudrate=self.baudrate, timeout=1)
            
            while shared.running:
                if ser.in_waiting > 0:
                    try:
                        # Đọc dòng dữ liệu thô (NMEA sentence) từ cảm biến gửi về
                        line = ser.readline().decode('utf-8', errors='ignore')
                        
                        # Lọc đúng chuỗi $GPRMC chứa đầy đủ Vĩ độ, Kinh độ và Vận tốc di chuyển
                        if line.startswith('$GPRMC'):
                            msg = pynmea2.parse(line)
                            
                            # Nếu Status = 'A' (Active) nghĩa là cảm biến đã khóa được vệ tinh thành công
                            if msg.status == 'A':  
                                shared.latitude = msg.latitude
                                shared.longitude = msg.longitude
                                shared.gps_valid = True
                                if msg.spd_over_grnd is not None:
                                    shared.gps_speed = msg.spd_over_grnd * 1.852  # Đổi Knot -> km/h
                            else:
                                # Nếu Status = 'V' (Void) nghĩa là cảm biến đang bật nhưng chưa bắt được sóng
                                shared.gps_valid = False 
                                
                    except pynmea2.ParseError:
                        continue
                    except Exception:
                        continue
                        
                # Nghỉ 100ms mỗi chu kỳ đọc để bảo vệ CPU không bị quá nhiệt
                time.sleep(0.1)  
                
            ser.close()
            print("[GPS] Đã ngắt kết nối cổng phần cứng an toàn.")
        except Exception as e:
            print(f"[GPS Error] Không thể mở cổng {self.port}. Hãy kiểm tra lại dây cắm! Chi tiết: {e}")
            shared.gps_valid = False

    def stop(self):
        pass
