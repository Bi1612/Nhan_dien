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

camera_thread = CameraThread()
yolo_thread = YOLOThread()
sensor_thread = SensorThread()
gps_thread = GPSThread()

camera_thread.start()
yolo_thread.start()
sensor_thread.start()
gps_thread.start()

try:

    while True:

        start_time = time.time()

        if shared.frame is None:

            time.sleep(0.01)

            continue

        frame = shared.frame.copy()

        lane_status = "CENTER"

        if shared.gps_speed > 30:

            lines = detect_lane_lines(frame)

            if lines is not None:

                left_x = 0
                right_x = frame.shape[1]

                for line in lines:

                    x1,y1,x2,y2 = line[0]

                    cv2.line(
                        frame,
                        (x1,y1),
                        (x2,y2),
                        (0,255,0),
                        2
                    )

                    if x1 < frame.shape[1]//2:

                        left_x = max(
                            left_x,
                            x1
                        )

                    else:

                        right_x = min(
                            right_x,
                            x1
                        )

                lane_status = check_lane_departure(
                    left_x,
                    right_x,
                    frame.shape[1]
                )

        latitude = shared.latitude

        longitude = shared.longitude

        speed_kmh = shared.gps_speed

        detections = shared.detections

        sign = detect_traffic_sign(frame)

        if sign == "SPEED_30":

            update_speed_limit(30)

        elif sign == "SPEED_50":

            update_speed_limit(50)

        elif sign == "SPEED_80":

            update_speed_limit(80)

        overspeed_status = check_overspeed(
            shared.gps_speed
        )

        shared.speed_limit = get_speed_limit()

        danger_zone = create_danger_zone(
            shared.gps_speed
        )

        draw_danger_zone(
            frame,
            danger_zone
        )

        fcw_status = check_forward_collision(
            detections,
            danger_zone,
            shared.gps_speed,
            shared.distance
        )

        warning_level = get_warning_level(
            fcw_status,
            lane_status,
            overspeed_status
        )

        fps = 1.0 / max(
            time.time() - start_time,
            0.001
        )

        for obj in detections:

            x1,y1,x2,y2 = map(
                int,
                obj["box"]
            )

            cls = obj["class"]

            cv2.rectangle(
                frame,
                (x1,y1),
                (x2,y2),
                (0,255,0),
                2
            )

            cv2.putText(
                frame,
                cls,
                (x1,y1-10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0,255,0),
                2
            )

        cv2.putText(
            frame,
            f"FCW: {fcw_status}",
            (20,40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0,0,255),
            2
        )

        cv2.putText(
            frame,
            f"Speed: {shared.gps_speed:.1f} km/h",
            (20,80),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255,255,0),
            2
        )

        cv2.putText(
            frame,
            f"LIMIT: {shared.speed_limit}",
            (20,120),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255,255,0),
            2
        )

        cv2.putText(
            frame,
            overspeed_status,
            (20,160),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0,0,255),
            2
        )

        cv2.putText(
            frame,
            f"LDW: {lane_status}",
            (20,200),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0,255,255),
            2
        )

        if lane_status != "CENTER":

            cv2.putText(
                frame,
                "LANE DEPARTURE",
                (120,120),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0,0,255),
                3
            )

        cv2.putText(
            frame,
            f"DIST: {shared.distance:.1f} cm",
            (20,240),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255,255,0),
            2
        )

        cv2.putText(
            frame,
            f"AX:{shared.ax:.0f}",
            (20,280),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255,255,0),
            2
        )

        cv2.putText(
            frame,
            f"LAT:{latitude:.4f}",
            (20,320),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255,255,255),
            1
        )

        cv2.putText(
            frame,
            f"LON:{longitude:.4f}",
            (20,360),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255,255,255),
            1
        )

        cv2.putText(
            frame,
            f"FPS:{fps:.1f}",
            (20,380),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0,255,0),
            2
        )

        cv2.putText(
            frame,
            f"SIGN: {sign}",
            (20,390),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0,255,255),
            2
        )

        cv2.putText(
            frame,
            f"WARNING: {warning_level}",
            (20,400),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0,0,255),
            2
        )

        if overspeed_status == "OVERSPEED":

            cv2.putText(
                frame,
                "SLOW DOWN!",
                (120,200),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0,0,255),
                3
            )

        cv2.imshow(
            "ADAS",
            frame
        )

        if cv2.waitKey(1) == ord("q"):
            break

except KeyboardInterrupt:
    pass

finally:

    shared.running = False

    camera_thread.stop()
    
    sensor_thread.stop()

    gps_thread.stop()

    camera_thread.join()

    yolo_thread.join()

    sensor_thread.join()

    gps_thread.join()

    cv2.destroyAllWindows()