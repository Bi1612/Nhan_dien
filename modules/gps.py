# ==========================
# GPS
# ==========================

from modules.gps_thread import GPSThread

# Khởi tạo GPS Thread
gps_thread = GPSThread()

# Chạy GPS Thread
gps_thread.start()

# Kích hoạt LDW khi tốc độ GPS > 30 km/h
if shared.gps_speed > 30:
    lines = detect_lane_lines(frame)

    if lines is not None:
        left_x = 0
        right_x = frame.shape[1]

        for line in lines:
            x1, y1, x2, y2 = line[0]

            cv2.line(
                frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )

            if x1 < frame.shape[1] // 2:
                left_x = max(left_x, x1)
            else:
                right_x = min(right_x, x1)

        lane_status = check_lane_departure(
            left_x,
            right_x,
            frame.shape[1]
        )

# Kiểm tra quá tốc độ
overspeed_status = check_overspeed(shared.gps_speed)

# Tạo vùng nguy hiểm theo tốc độ GPS
danger_zone = create_danger_zone(shared.gps_speed)

# FCW sử dụng tốc độ GPS
fcw_status = check_forward_collision(
    detections,
    danger_zone,
    shared.gps_speed,
    shared.distance
)

# Hiển thị tốc độ GPS
cv2.putText(
    frame,
    f"Speed: {shared.gps_speed:.1f} km/h",
    (20, 80),
    cv2.FONT_HERSHEY_SIMPLEX,
    0.8,
    (255, 255, 0),
    2
)
