import threading
import serial
import time

import modules.shared_data as shared

class SensorThread(threading.Thread):

    def __init__(self):

        super().__init__()

        self.daemon = True

        self.ser = serial.Serial(
            "/dev/ttyACM0",
            115200,
            timeout=1
        )

    def run(self):
        
        # [TINH CHỈNH] Xóa sạch bộ đệm tồn đọng ngay khi vừa khởi động luồng
        try:
            self.ser.reset_input_buffer()
        except:
            pass

        while shared.running:

            try:
                # [TINH CHỈNH] CHỐNG TRÀN BUFFER
                # Nếu Jetson Nano xử lý YOLO quá lâu làm dữ liệu Serial bị dồn ứ (> 100 ký tự)
                # Ta chủ động xóa toàn bộ để ép hệ thống đọc gói tin mới nhất ở thời gian thực
                if self.ser.in_waiting > 100:
                    self.ser.reset_input_buffer()

                line = self.ser.readline()
                
                # [TINH CHỈNH] SỬA LỖI DECODE CHUỖI
                # Thêm errors='ignore' để nếu dòng đầu tiên bị mất byte hoặc dính ký tự rác
                # thì luồng không bị crash ngầm xuống khối except khiến khoảng cách bị kẹt ở 999
                line = line.decode('utf-8', errors='ignore').strip()

                data = line.split(",")

                if len(data) != 4:
                    continue

                raw_distance = float(data[0])
                ax = float(data[1])
                ay = float(data[2])
                az = float(data[3])

                # [TINH CHỈNH] BỘ LỌC THÔNG THẤP (LOW-PASS FILTER) CHO HC-SR04
                # Nếu dữ liệu thô gửi lên là mã lỗi (999) hoặc hệ thống chưa có dữ liệu ban đầu thì gán thẳng
                if shared.distance is None or shared.distance == 0 or shared.distance == 999.0 or raw_distance == 999.0:
                    shared.distance = raw_distance
                else:
                    # Nếu là khoảng cách thực tế, bộ lọc giữ lại 80% độ ổn định của khung hình cũ
                    # và bù thêm 20% thay đổi của khung hình mới để làm mượt, triệt tiêu xung nhiễu nhảy số
                    shared.distance = (0.8 * shared.distance) + (0.2 * raw_distance)

                shared.ax = ax
                shared.ay = ay
                shared.az = az

            except:
                # Nếu có lỗi bất ngờ, ta cứ để pass để luồng tiếp tục vòng lặp sau mà không bị chết đứng
                pass

            time.sleep(0.01)

    def stop(self):

        self.ser.close()
