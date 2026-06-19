import threading
import serial
import time

import modules.shared_data as shared

class SensorThread(threading.Thread):

    def __init__(self):
        super().__init__()
        self.daemon = True

        # Giữ nguyên cấu hình cổng kết nối tới Arduino/ESP32 của gậy dò đường
        self.ser = serial.Serial(
            "/dev/ttyACM0",
            115200,
            timeout=1
        )

    def run(self):
        print("[INFO] Luồng cảm biến siêu âm & IMU đã kích hoạt...")
        while shared.running:
            try:
                if self.ser.in_waiting > 0:
                    line = self.ser.readline()
                    line = line.decode().strip()
                    data = line.split(",")

                    if len(data) != 4:
                        continue

                    distance = float(data[0])
                    ax = float(data[1])
                    ay = float(data[2])
                    az = float(data[3])

                    # Đẩy dữ liệu ra bộ nhớ chia sẻ thời gian thực
                    shared.distance = distance
                    shared.ax = ax
                    shared.ay = ay
                    shared.az = az

            except Exception as e:
                # Tránh in log lỗi liên tục làm chậm hệ thống, chỉ pass để bỏ qua gói tin lỗi
                pass

            # Chu kỳ quét 10ms (100Hz) phù hợp tốc độ phản hồi cảm biến khoảng cách
            time.sleep(0.01)

    def stop(self):
        if self.ser.is_open:
            self.ser.close()
