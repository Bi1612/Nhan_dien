import cv2
import time

import modules.shared_data as shared

from modules.camera_thread import CameraThread
from modules.yolo_thread import YOLOThread
from modules.sensor_thread import SensorThread
from modules.gps_thread import GPSThread

from modules.danger_zone import (
    create_danger_zone,
    draw_danger_zone
)

from modules.fcw import (
    check_forward_collision
)

camera_thread = CameraThread()
yolo_thread = YOLOThread()
sensor_thread = SensorThread()
gps_thread = GPSThread()

camera_thread.start()
yolo_thread.start()
sensor_thread.start()
gps_thread.start()

while True:

    if shared.frame is None:
        continue

    frame = shared.frame.copy()

    detections = shared.detections

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

    for obj in detections:

        x1, y1, x2, y2 = map(
            int,
            obj["box"]
        )

        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            (0, 255, 0),
            2
        )

    cv2.putText(
        frame,
        f"FCW:{fcw_status}",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 0, 255),
        2
    )

    cv2.putText(
        frame,
        f"DIST:{shared.distance:.1f} cm",
        (20, 80),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 0),
        2
    )

    cv2.putText(
        frame,
        f"SPEED:{shared.gps_speed:.1f}",
        (20, 120),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 0),
        2
    )

    cv2.imshow(
        "FCW",
        frame
    )

    if cv2.waitKey(1) == ord("q"):
        break
