import cv2
import time

import modules.shared_data as shared

from modules.camera_thread import CameraThread
from modules.gps_thread import GPSThread

from modules.traffic_sign import (
    detect_traffic_sign
)

from modules.speed_limit_manager import (
    update_speed_limit,
    get_speed_limit
)

from modules.overspeed import (
    check_overspeed
)

camera_thread = CameraThread()
gps_thread = GPSThread()

camera_thread.start()
gps_thread.start()

while True:

    if shared.frame is None:
        continue

    frame = shared.frame.copy()

    sign = detect_traffic_sign(frame)

    if sign == "SPEED_30":
        update_speed_limit(30)

    elif sign == "SPEED_50":
        update_speed_limit(50)

    elif sign == "SPEED_80":
        update_speed_limit(80)

    speed_limit = get_speed_limit()

    overspeed_status = check_overspeed(
        shared.gps_speed
    )

    cv2.putText(
        frame,
        f"SIGN:{sign}",
        (20,40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0,255,255),
        2
    )

    cv2.putText(
        frame,
        f"LIMIT:{speed_limit}",
        (20,80),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255,255,0),
        2
    )

    cv2.putText(
        frame,
        f"SPEED:{shared.gps_speed:.1f}",
        (20,120),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
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

    cv2.imshow(
        "TRAFFIC SIGN",
        frame
    )

    if cv2.waitKey(1)==ord("q"):
        break