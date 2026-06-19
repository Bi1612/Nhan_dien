import threading
import time
import serial
import modules.shared_data as shared

class SensorThread(threading.Thread):
    def __init__(self):
        super(SensorThread, self).__init__()
        # Cấu hình chính xác cổng Serial vật lý nối với Arduino trên Jetson Linux
        self.port = '/dev/ttyACM0'
        self.baudrate = 9600
        self.stopped = False
        self.ser = None
        
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            print(f"[HARDWARE] Kết nối Serial thành công với Arduino tại cổng: {self.port}")
        except Exception as e:
            print(f"[HARDWARE ERROR] Không tìm thấy mạch Arduino tại {self.port}. Chi tiết: {e}")

    def run(self):
        while not self.stopped:
            if self.ser and self.ser.is_open:
                try:
                    if self.ser.in_central > 0:
                        line = self.ser.readline().decode('utf-8').strip()
                        if line:
                            shared.distance = float(line)
                except Exception as e:
                    # Tránh crash hệ thống nếu dây siêu âm lỏng hoặc mất kết nối đột ngột
                    shared.distance = 999.0
            time.sleep(0.05)

    def stop(self):
        self.stopped = True
        if self.ser and self.ser.is_open:
            self.ser.close()
