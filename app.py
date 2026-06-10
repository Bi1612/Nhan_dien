# ==============================================================================
# HỆ THỐNG HỖ TRỢ LÁI XE NÂNG CAO (ADAS) - PHÂN HỆ ĐIỀU KHIỂN CHÍNH
# ==============================================================================
# Tệp tin: main.py
# Mô tả: Chu kỳ xử lý trung tâm (Main Loop) điều phối luồng dữ liệu từ 
#        Camera, cảm biến khoảng cách, GPS và mô hình YOLO để đưa ra 
#        cảnh báo va chạm (FCW), chệch làn (LDW) và quá tốc độ.
# Tiêu chuẩn áp dụng: Ganssle Group Embedded Code Standard
# ==============================================================================

import cv2
import time

import modules.shared_data as shared

from modules.camera_thread import CameraThread
from modules.yolo_thread import YOLOThread
from modules.danger_zone import (
    create_danger_zone,
    draw_danger_zone
)
from modules.fcw import (
    check_forward_collision
)
from modules.sensor_thread import SensorThread
from modules.gps_thread import GPSThread
from modules.traffic_sign import (
    detect_traffic_sign
)
from modules.speed_limit_manager import (
    update_speed_limit
)
from modules.speed_limit_manager import (
    get_speed_limit
)
from modules.overspeed import (
    check_overspeed
)
from modules.lane_detection import (
    detect_lane_lines
)
from modules.lane_departure import (
    check_lane_departure
)
from modules.warning_controller import (
    get_warning_level
)

from modules.audio_alert import (
    play_alert
)

# ------------------------------------------------------------------------------
# KHỞI TẠO VÀ KÍCH HOẠT CÁC LUỒNG NGOẠI VI / ĐỒNG BỘ (THREADS)
# ------------------------------------------------------------------------------
camera_thread = CameraThread()
yolo_thread = YOLOThread()
sensor_thread = SensorThread()
gps_thread = GPSThread()

camera_thread.start()
yolo_thread.start()
sensor_thread.start()
gps_thread.start()

try:
    # --------------------------------------------------------------------------
    # VÒNG LẶP XỬ LÝ CHÍNH (MAIN CONTROL LOOP)
    # --------------------------------------------------------------------------
    while True:

        # Đo đạc mốc thời gian thực để phục vụ tính toán tần suất xử lý (FPS)
        start_time = time.time()

        # Cơ chế đồng bộ: Chờ cho đến khi Camera Thread nạp dữ liệu frame đầu tiên.
        # Nghỉ 10ms để nhường tài nguyên CPU cho các luồng phần cứng khác.
        if shared.frame is None:
            time.sleep(0.01)
            continue

        # Tạo bản sao cục bộ để tránh hiện tượng Race Condition (xung đột ghi dữ liệu)
        # khi Camera Thread cập nhật vùng nhớ shared.frame liên tục.
        frame = shared.frame.copy()

        # Trạng thái mặc định khi xe di chuyển an toàn trong làn
        lane_status = "CENTER"

        # Ngưỡng vận tốc an toàn (>30km/h): Theo tiêu chuẩn ADAS, thuật toán LDW 
        # chỉ kích hoạt ở tốc độ trung bình/cao để tránh báo động giả trong đô thị.
        if shared.gps_speed > 30:
            lines = detect_lane_lines(frame)

            if lines is not None:
                left_x = 0
                right_x = frame.shape[1]

                for line in lines:
                    x1, y1, x2, y2 = line[0]

                    # Vẽ trực quan hóa các đường biên làn phục vụ quá trình debug trực tiếp
                    cv2.line(
                        frame,
                        (x1, y1),
                        (x2, y2),
                        (0, 255, 0),
                        2
                    )

                    # Phân loại vạch kẻ làn dựa trên trục đối xứng trung tâm của khung hình
                    if x1 < frame.shape[1] // 2:
                        left_x = max(left_x, x1)
                    else:
                        right_x = min(right_x, x1)

                # Thuật toán tính toán độ lệch tâm để xác định xu hướng đè vạch
                lane_status = check_lane_departure(
                    left_x,
                    right_x,
                    frame.shape[1]
                )

        # Chụp lại trạng thái snapshot của bộ nhớ chia sẻ tại chu kỳ hiện tại
        latitude = shared.latitude
        longitude = shared.longitude
        speed_kmh = shared.gps_speed
        detections = shared.detections

        # Phân tích thị giác máy tính để trích xuất biển báo tốc độ (nếu có)
        sign = detect_traffic_sign(frame)

        # Máy trạng thái cập nhật luật tốc độ thực tế từ hạ tầng giao thông
        if sign == "SPEED_30":
            update_speed_limit(30)
        elif sign == "SPEED_50":
            update_speed_limit(50)
        elif sign == "SPEED_80":
            update_speed_limit(80)

        # Tính toán trạng thái vi phạm tốc độ dựa trên giới hạn hiện hành
        overspeed_status = check_overspeed(shared.gps_speed)
        shared.speed_limit = get_speed_limit()

        # Vùng nguy hiểm (Danger Zone) thay đổi biên độ dựa theo hàm vận tốc thực tế
        danger_zone = create_danger_zone(shared.gps_speed)
        draw_danger_zone(frame, danger_zone)

        # Thuật toán FCW: Đánh giá nguy cơ va chạm dựa trên khoảng cách cảm biến 
        # và sự xuất hiện của hộp tọa độ (Bounding Box) nằm trong Vùng Nguy Hiểm.
        fcw_status = check_forward_collision(
            detections,
            danger_zone,
            shared.gps_speed,
            shared.distance
        )

        # Bộ điều khiển trung tâm chấm điểm nguy cơ tổng hợp để kích hoạt còi/đèn cảnh báo
        warning_level = get_warning_level(
            fcw_status,
            lane_status,
            overspeed_status
        )

        # Tính toán hiệu năng: Giới hạn mẫu số ở mức 0.001s để chặn lỗi chia cho 0 (ZeroDivisionError)
        fps = 1.0 / max(time.time() - start_time, 0.001)

        # --------------------------------------------------------------------------
        # PHẦN TỬ HÌNH ẢNH & GIAO DIỆN NGƯỜI DÙNG (OSD / TELEMETRY OVERLAY)
        # --------------------------------------------------------------------------
        for obj in detections:
            x1, y1, x2, y2 = map(int, obj["box"])
            cls = obj["class"]

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )
            cv2.putText(
                frame,
                cls,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2
            )

        cv2.putText(
            frame,
            f"FCW: {fcw_status}",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            2
        )
        cv2.putText(
            frame,
            f"Speed: {shared.gps_speed:.1f} km/h",
            (20, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 0),
            2
        )
        cv2.putText(
            frame,
            f"LIMIT: {shared.speed_limit}",
            (20, 120),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 0),
            2
        )
        cv2.putText(
            frame,
            overspeed_status,
            (20, 160),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            2
        )
        cv2.putText(
            frame,
            f"LDW: {lane_status}",
            (20, 200),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 255),
            2
        )

        # Kích hoạt cảnh báo đồ họa trực quan mức 1: Chệch làn đường
        if lane_status != "CENTER":
            cv2.putText(
                frame,
                "LANE DEPARTURE",
                (120, 120),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                3
            )

        cv2.putText(
            frame,
            f"DIST: {shared.distance:.1f} cm",
            (20, 240),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 0),
            2
        )
        cv2.putText(
            frame,
            f"AX:{shared.ax:.0f}",
            (20, 280),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 0),
            2
        )
        cv2.putText(
            frame,
            f"LAT:{latitude:.4f}",
            (20, 320),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1
        )
        cv2.putText(
            frame,
            f"LON:{longitude:.4f}",
            (20, 360),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1
        )
        cv2.putText(
