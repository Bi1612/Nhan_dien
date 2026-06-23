import threading
import serial
import pynmea2
import modules.shared_data as shared

class GPSThread(threading.Thread):
    # SỬA LẠI ĐÂY: Thay '/dev/ttyUSB0' thành '/dev/ttyTHS1' để đọc trực tiếp chân GPIO
    def __init__(self, port='/dev/ttyTHS1', baudrate=9600):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.daemon = True  # Tự động giải phóng luồng khi tắt app chính

    def run(self):
        import time # Ép nạp cục bộ chống xung đột môi trường nhúng
        print(f"[GPS GPIO] Đang kết nối cổng UART chân rết {self.port} với Baudrate {self.baudrate}...")
        
        # Khởi tạo giá trị nền ban đầu
        shared.latitude = 0.0
        shared.longitude = 0.0
        shared.gps_speed = 0.0
        shared.gps_valid = False  # Mặc định ban đầu báo chưa có sóng vệ tinh
        
        try:
            # Mở cổng Serial UART trực tiếp từ chân GPIO của Jetson
            ser = serial.Serial(self.port, baudrate=self.baudrate, timeout=1)
            
            while shared.running:
                if ser.in_waiting > 0:
                    try:
                        line = ser.readline().decode('utf-8', errors='ignore')
                        
                        if line.startswith('$GPRMC'):
                            msg = pynmea2.parse(line)
                            
                            if msg.status == 'A':  # Đã khóa vệ tinh thành công
                                shared.latitude = msg.latitude
                                shared.longitude = msg.longitude
                                shared.gps_valid = True
                                if msg.spd_over_grnd is not None:
                                    shared.gps_speed = msg.spd_over_grnd * 1.852  # Đổi Knot -> km/h
                            else:
                                shared.gps_valid = False # Thiết bị đang bật nhưng chưa bắt được sóng ngoài trời
                                
                    except pynmea2.ParseError:
                        continue
                    except Exception:
                        continue
                        
                time.sleep(0.1)  # Nghỉ 100ms mỗi chu kỳ đọc để bảo vệ CPU
                
            ser.close()
            print("[GPS] Đã ngắt kết nối cổng UART an toàn.")
        except Exception as e:
            print(f"[GPS Error] Không thể mở cổng GPIO {self.port}. Chi tiết: {e}")
            shared.gps_valid = False

    def stop(self):
        pass
