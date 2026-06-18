# ==============================================================================
# HỆ THỐNG TRÍ TUỆ NHÂN TẠO HỖ TRỢ NGƯỜI KHIẾM THỊ - PHÂN HỆ ĐIỀU KHIỂN CHÍNH
# ==============================================================================
# Tệp tin: app.py
# Mô tả: Điều phối luồng dữ liệu từ Camera, Cảm biến siêu âm và mô hình YOLOv5 TensorRT.
#        Áp dụng cơ chế khởi chạy giãn cách luồng để tối ưu hóa tài nguyên RAM/GPU.
# ==============================================================================

import cv2
import time

import modules.shared_data as shared

from modules.camera_thread import CameraThread
from modules.yolo_thread import YOLOThread
from modules.fcw import check_forward_collision
from modules.sensor_thread import SensorThread
from modules.warning_controller import get_warning_level

# ------------------------------------------------------------------------------
# KHỞI TẠO CÁC ĐỐI TƯỢNG LUỒNG (THREADS INITIALIZATION)
# ------------------------------------------------------------------------------
camera_thread = CameraThread()
yolo_thread = YOLOThread()
sensor_thread = SensorThread()

# ------------------------------------------------------------------------------
# CƠ CHẾ KHỞI CHẠY GIÃN CÁCH LUỒNG (THREAD BOOTING DELAY FOR TENSORRT)
# ------------------------------------------------------------------------------
print("\n" + "="*60)
print("[HỆ THỐNG] BẮT ĐẦU KHỞI ĐỘNG PHÂN HỆ HỖ TRỢ NGƯỜI MÙ...")
print("="*60)

# Bước 1: Kích hoạt luồng YOLO để nạp mô hình TensorRT .engine nặng vào GPU trước
yolo_thread.start()
print("[HỆ THỐNG] Đang tiến hành nạp mô hình YOLOv5n TensorRT vào GPU...")
print("[HỆ THỐNG] Vui lòng đợi từ 5 - 7 giây để hệ thống phân phối bộ nhớ RAM/Swap...")

# Ép chương trình chính tạm dừng 7 giây để luồng phụ YOLOThread hoàn thành việc load model
time.sleep(7) 

# Bước 2: Sau khi mô hình đã nạp xong xuôi, mới kích hoạt Camera và Cảm biến siêu âm Arduino
print("[HỆ THỐNG] Mô hình AI sẵn sàng! Tiến hành kích hoạt các luồng ngoại vi...")
camera_thread.start()
sensor_thread.start()
print("[HỆ THỐNG] Tất cả các luồng đã hoạt động thông suốt. Bắt đầu vòng lặp chính.")
print("="*60 + "\n")

try:
    # --------------------------------------------------------------------------
    # VÒNG LẶP XỬ LÝ CHÍNH TRÊN JETSON NANO (MAIN CONTROL LOOP)
    # --------------------------------------------------------------------------
    while True:
        start_time = time.time()

        # Cơ chế đồng bộ: Chờ cho đến khi Camera Thread nạp dữ liệu frame đầu tiên.
        if shared.frame is None:
            time.sleep(0.01)
            continue

        # Tạo bản sao cục bộ để tránh hiện tượng Race Condition khi đa luồng cập nhật
        frame = shared.frame.copy()
        detections = shared.detections

        # Gọi thuật toán kết hợp cảm biến (Sensor Fusion) xử lý bài toán 4m của cô giáo
        fcw_status = check_forward_collision(
            detections,
            None, 
            shared.gps_speed,
            shared.distance
        )

        # Bộ điều khiển trung tâm ra quyết định trạng thái còi báo động cho người mù
        warning_level = get_warning_level(fcw_status)

        # Tính toán tần suất đáp ứng xử lý khung hình tại biên (Hệ thống FPS)
        fps = 1.0 / max(time.time() - start_time, 0.001)

        # --------------------------------------------------------------------------
        # ĐỒ HỌA TRỰC QUAN HÓA OVERLAY PHỤC VỤ QUÁ TRÌNH PHÒNG THÍ NGHIỆM (MÀN HÌNH 7 INCH)
        # --------------------------------------------------------------------------
        for obj in detections:
            x1, y1, x2, y2 = map(int, obj["box"])
            cls = obj["class"]

            # Chỉ vẽ khung bọc cho các class cần thiết phục vụ người đi bộ
            if cls in ["person", "car", "truck", "bus", "motorcycle"]:
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, cls, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # Hiển thị thông số thực nghiệm độc lập cho bài toán người mù lên giao diện 7 inch
        cv2.putText(frame, f"KICH BAN CO GIAO: {fcw_status}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.putText(frame, f"WARNING LEVEL: {warning_level}", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
        cv2.putText(frame, f"SIEU AM: {shared.distance:.1f} cm", (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        cv2.putText(frame, f"HE THONG SYSTEM FPS: {fps:.1f}", (20, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)

        # Đẩy luồng hình ảnh hiển thị trực tiếp lên màn hình giám sát 7 inch
        cv2.imshow("Blind Support System Test", frame)
        
        # Nhấn phím 'q' trên bàn phím kết nối Jetson Nano để thoát chương trình an toàn
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except KeyboardInterrupt:
    print("[HỆ THỐNG] Ngắt chương trình bằng tổ hợp phím bàn phím.")

finally:
    # Hạ cờ chạy ngầm để dọn dẹp và giải phóng tài nguyên hệ thống
    shared.running = False
    cv2.destroyAllWindows()
    print("[HỆ THỐNG] Đã giải phóng toàn bộ tài nguyên phần cứng an toàn. Kết thúc.")
