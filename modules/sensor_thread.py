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
        
        # Xóa sạch bộ đệm tồn đọng ngay khi vừa khởi động luồng
        try:
            self.ser.reset_input_buffer()
        except:
            pass

        while shared.running:

            try:
                # CHỐNG TRÀN BUFFER (Sửa lỗi treo lệnh cat / đen màn hình screen)
                # Nếu Jetson Nano bận xử lý YOLO làm dữ liệu Serial bị dồn ứ quá nhiều (> 100 ký tự)
                # Ta chủ động xóa sạch để ép hệ thống đọc gói tin mới nhất ở thời gian thực
                if self.ser.in_waiting > 100:
                    self.ser.reset_input_buffer()

                line = self.ser.readline()
                
                # SỬA LỖI DECODE CHUỖI
                # Thêm errors='ignore' để nếu khung hình đầu bị mất byte hoặc dính ký tự rác
                # thì luồng không bị nhảy xuống khối except (không bị kẹt ở số 999)
                line = line.decode('utf-8', errors='ignore').strip()

                data = line.split(",")

                if len(data) != 4:
                    continue

                raw_distance = float(data[0])
                ax = float(data[1])
                ay = float(data[2])
                az = float(data[3])

                # BỘ LỌC THÔNG THẤP (LOW-PASS FILTER) LÀM MƯỢT KHOẢNG CÁCH
                # Nếu dữ liệu thô gửi lên là mã lỗi (999) hoặc hệ thống chưa có dữ liệu ban đầu thì gán thẳng
                if shared.distance is None or shared.distance == 0 or shared.distance == 999.0 or raw_distance == 999.0:
                    shared.distance = raw_distance
                else:
                    # Bộ lọc giữ lại 80% độ ổn định của khung hình cũ
                    # và bù thêm 20% thay đổi của khung hình mới để triệt tiêu xung nhiễu nhảy số
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
