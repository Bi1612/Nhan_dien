# ==============================================================================
# HỆ THỐNG TRÍ TUỆ NHÂN TẠO HỖ TRỢ NGƯỜI KHIẾM THỊ - PHÂN HỆ ĐIỀU KHIỂN CHÍNH
# ==============================================================================

import cv2
import time

import modules.shared_data as shared

from modules.camera_thread import CameraThread
from modules.yolo_thread import YOLOThread
from modules.fcw import check_forward_collision
from modules.sensor_thread import SensorThread
from modules.warning_controller import get_warning_level
from modules.audio_alert import play_alert

# ------------------------------------------------------------------------------
# KHỞI TẠO VÀ KÍCH HOẠT CÁC LUỒNG NGOẠI VI (CAMERA & SIÊU ÂM ARDUINO)
# ------------------------------------------------------------------------------
camera_thread = CameraThread()
yolo_thread = YOLOThread()
sensor_thread = SensorThread()

camera_thread.start()
yolo_thread.start()
sensor_thread.start()

print("[HỆ THỐNG] Đã khởi động các luồng cảm biến. Sẵn sàng thử nghiệm bài toán 4 mét.")

try:
    # --------------------------------------------------------------------------
    # VÒNG LẶP XỬ LÝ CHÍNH TRÊN JETSON NANO (MAIN CONTROL LOOP)
    # --------------------------------------------------------------------------
    while True:
        start_time = time.time()

        if shared.frame is None:
            time.sleep(0.01)
            continue

        # Tạo bản sao cục bộ để tránh hiện tượng Race Condition khi đa luồng cập nhật
        frame = shared.frame.copy()
        detections = shared.detections

        # Gọi thuật toán kết hợp cảm biến (Sensor Fusion) xử lý bài toán 4m của cô giáo
        # Bỏ qua tham số vùng đa giác hình học cũ của ô tô (truyền None)
        fcw_status = check_forward_collision(
            detections,
            None, 
            shared.gps_speed,
            shared.distance
        )

        # Bộ điều khiển trung tâm ra quyết định trạng thái còi báo động
        warning_level = get_warning_level(fcw_status)

        # Tính toán tần suất đáp ứng xử lý khung hình tại biên (FPS)
        fps = 1.0 / max(time.time() - start_time, 0.001)

        # --------------------------------------------------------------------------
        # ĐỒ HỌA TRỰC QUAN HÓA OVERLAY PHỤC VỤ QUÁ TRÌNH PHÒNG THÍ NGHIỆM
        # --------------------------------------------------------------------------
        for obj in detections:
            x1, y1, x2, y2 = map(int, obj["box"])
            cls = obj["class"]

            if cls in ["person", "car", "truck", "bus", "motorcycle"]:
                # Vẽ khung bọc định vị đối tượng
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, cls, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # Hiển thị Telemetry trạng thái lên màn hình điều khiển
        cv2.putText(frame, f"KICH BAN CO GIAO: {fcw_status}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.putText(frame, f"WARNING LEVEL: {warning_level}", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
        cv2.putText(frame, f"SIEU AM: {shared.distance:.1f} cm", (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        cv2.putText(frame, f"HE THONG SYSTEM FPS: {fps:.1f}", (20, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)

        # Hiển thị luồng video xử lý lên màn hình giám sát để theo dõi cự ly pixel Bounding Box
        cv2.imshow("Blind Support System Test", frame)
        
        # Nhấn phím 'q' trên bàn phím kết nối Jetson Nano để thoát chương trình an toàn
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except KeyboardInterrupt:
    print("[HỆ THỐNG] Ngắt chương trình bằng bàn phím.")

finally:
    shared.running = False
    cv2.destroyAllWindows()
    print("[HỆ THỐNG] Đã giải phóng tài nguyên phần cứng an toàn.")
