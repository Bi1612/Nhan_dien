import threading
import time
import serial
import modules.shared_data as shared

class SensorThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True
        # Cấu hình cổng Serial kết nối Arduino (Tự động thích ứng cổng nhúng Jetson)
        self.port = "/dev/ttyUSB0" # Hoặc thay thành "/dev/ttyACM0" nếu Arduino nhận cổng ACM
        self.baudrate = 115200
        self.ser = None

    def run(self):
        # Vòng lặp cố gắng kết nối ngoại vi Serial UART với Arduino UNO R3
        while shared.running and self.ser is None:
            try:
                self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
                print(f"[SENSOR] Da ket noi thanh cong voi Arduino tai cong: {self.port}")
            except Exception as e:
                print(f"[SENSOR] Dang doi cam phan cung Arduino... Loi: {e}")
                time.sleep(2)

        # Luồng xử lý bóc tách chuỗi khoảng cách liên tục
        while shared.running and self.ser:
            try:
                if self.ser.in_waiting > 0:
                    line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    
                    if line:
                        # Trường hợp 1: Arduino chỉ in ra một con số khoảng cách thuần túy dạng cm
                        if line.isdigit():
                            val = float(line)
                            if 2 <= val <= 400: # Ngưỡng vật lý của cảm biến HC-SR04
                                shared.distance = val
                        # Trường hợp 2: Arduino gửi chuỗi chứa tiền tố (Ví dụ: "DIST:120.5")
                        elif "DIST" in line or "D:" in line:
                            parts = line.split(':')
                            if len(parts) >= 2 and parts[1].strip().replace('.', '', 1).isdigit():
                                val = float(parts[1].strip())
                                shared.distance = val
                                
            except Exception as e:
                print(f"[SENSOR] Loi doc dong du lieu Serial: {e}")
                time.sleep(0.1)
                
        if self.ser:
            self.ser.close()
