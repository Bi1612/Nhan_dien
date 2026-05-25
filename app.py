import cv2
import time
import modules.shared_data as shared

from modules.camera_thread import CameraThread
from modules.yolo_thread import YOLOThread
from modules.lane_thread import LaneThread

from datetime import datetime

from config import *
from modules.lane_detection import draw_lanes
from modules.collision_warning import (
    check_collision
)
from modules.dashboard import draw_dashboard
from modules.blackbox import (
    start_recording,
    write_frame,
    stop_recording
)

from modules.gps_module import read_gps

from modules.speed_warning import check_speed

from modules.blackbox import log_gps

from modules.traffic_sign import detect_traffic_sign

from modules.sensor_thread import SensorThread

from modules.sensor_fusion import evaluate_risk

from modules.drowsiness import detect_drowsiness

from modules.audio_alert import play_warning

from modules.ai_decision import evaluate_ai_state

from modules.tracker import (
    init_tracker,
    update_tracker
)

camera_thread = CameraThread()
yolo_thread = YOLOThread()
lane_thread = LaneThread()
sensor_thread = SensorThread()


camera_thread.start()
yolo_thread.start()
lane_thread.start()
sensor_thread.start()


start_recording()

frame_counter = 0

drowsiness_status = "AWAKE"

last_audio_time = 0
    
AUDIO_DELAY = 3
try:

    while True:

        sensor_distance = shared.sensor_distance

        ax = shared.ax
        ay = shared.ay
        az = shared.az

        if shared.frame is None:
            time.sleep(0.01)
            continue

        frame = shared.frame.copy()

        frame_counter += 1

        if frame_counter % 5 == 0:

            drowsiness_status = detect_drowsiness(
                frame
            )

        detections = shared.detections

        lines = shared.lines

        start_time = time.time()

        # Read GPS data
        latitude, longitude, speed_kmh = read_gps()

        acceleration = (
            ax**2 + ay**2 + az**2
        ) ** 0.5

        fusion_status = evaluate_risk(
            sensor_distance,
            speed_kmh,
            acceleration
        )

        log_gps(
            latitude,
            longitude,
            speed_kmh
        )

        frame = cv2.resize(
            frame,
            (FRAME_WIDTH, FRAME_HEIGHT)
        )

        tracked_box = update_tracker(frame)

        # Nếu tracker mất target thì detect lại
        if tracked_box is None and len(detections) > 0:

            largest_area = 0

            best_obj = None

            for obj in detections:

                class_name = obj['class']

                if class_name not in [
                    "car",
                    "bus",
                    "truck",
                    "motorcycle"
                ]:
                    continue

                x1, y1, x2, y2 = map(
                    int,
                    obj['box']
                )

                area = (
                    (x2 - x1) *
                    (y2 - y1)
                )

                if area > largest_area:

                    largest_area = area

                    best_obj = obj

            if best_obj is not None:

                x1, y1, x2, y2 = map(
                    int,
                    best_obj['box']
                )

                bbox = (
                    x1,
                    y1,
                    x2 - x1,
                    y2 - y1
                )

                init_tracker(frame, bbox)

                tracked_box = update_tracker(frame)


        if tracked_box is not None:

            x, y, w, h = map(
                int,
                tracked_box
            )

            cv2.rectangle(
                frame,
                (x, y),
                (x + w, y + h),
                (255, 255, 0),
                3
            )

        # ======================================================
        # Detect traffic signs
        # ======================================================

        sign_type, sign_box = detect_traffic_sign(frame)

        if sign_type is None:
            sign_type = "NONE"

        draw_lanes(frame, lines)

        person_count = 0
        car_count = 0

        nearest_distance = 999.0
        fcw_text = "SAFE"

        warning_levels = []

        for obj in detections:

            class_name = obj['class']

            if class_name not in ADAS_CLASSES:
                continue

            x1, y1, x2, y2 = map(int, obj['box'])

            color = COLORS.get(class_name, (255, 255, 255))

            distance = sensor_distance

            if distance < nearest_distance:
                nearest_distance = distance

            collision_status = check_collision(distance)

            warning_levels.append(collision_status)

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                color,
                2
            )

            label = f"{class_name} {distance:.1f}m"

            cv2.putText(
                frame,
                label,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                2
            )

            if class_name == "person":
                person_count += 1

            elif class_name == "car":
                car_count += 1

        if "DANGER" in warning_levels:
            fcw_text = "DANGER"

        elif "WARNING" in warning_levels:
            fcw_text = "WARNING"

        else:
            fcw_text = "SAFE"

        if speed_kmh is None:
            speed_kmh = 0.0

        speed_status = check_speed(speed_kmh)

        lane_warning = "LANE OK"

        if lines is None:
            lane_warning = "LANE LOST"

        ai_status = evaluate_ai_state(
            fcw_text,
            lane_warning,
            drowsiness_status,
            speed_status
        )

        current_audio_time = time.time()

        if ai_status == "EMERGENCY":

            if current_audio_time - last_audio_time > AUDIO_DELAY:

                play_warning(
                    "Collision Warning"
                )

                last_audio_time = current_audio_time


        if ai_status == "DRIVER FATIGUE":

            if current_audio_time - last_audio_time > AUDIO_DELAY:

                play_warning(
                    "Driver Drowsy"
                )

                last_audio_time = current_audio_time

        # ======================================================
        # Draw traffic sign detection
        # ======================================================

        if sign_box is not None:

            x, y, w, h = sign_box

            cv2.rectangle(
                frame,
                (x, y),
                (x + w, y + h),
                (0, 0, 255),
                3
            )

            cv2.putText(
                frame,
                sign_type,
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2
            )

        

        end_time = time.time()

        fps = 1 / max(end_time - start_time, 0.0001)

        latency = (end_time - start_time) * 1000

        draw_dashboard(
            frame,
            fps,
            latency,
            car_count,
            person_count,
            lane_warning,
            fcw_text,
            nearest_distance,
            sign_type
        )

        current_time = datetime.now().strftime("%H:%M:%S")

        cv2.putText(
            frame,
            current_time,
            (300, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2
        )

        if speed_status == "OVERSPEED":

            cv2.putText(
                frame,
                "SLOW DOWN!",
                (120, 200),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.2,
                (0, 0, 255),
                3
            )

        cv2.putText(
                frame,
                "JETSON NANO ADAS",
                (120, 400),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )
        
        cv2.putText(
                frame,
                f"RISK: {fusion_status}",
                (20, 320),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2
            )
        
        cv2.putText(
                frame,
                f"ACC X:{ax:.2f}",
                (20, 350),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255,255,0),
                2
            )
        
        cv2.putText(
            frame,
            f"DRIVER: {drowsiness_status}",
            (20, 380),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 255),
            2
        )

        cv2.imshow("ADAS SYSTEM", frame)

        write_frame(frame)

        key = cv2.waitKey(1)

        time.sleep(0.005)

        if key == ord('q'):
            break


except KeyboardInterrupt:

    print("Stopping ADAS...")

finally:

    shared.running = False

    camera_thread.stop()

    camera_thread.join()
    yolo_thread.join()
    lane_thread.join()
    sensor_thread.join()

    stop_recording()

    cv2.destroyAllWindows()