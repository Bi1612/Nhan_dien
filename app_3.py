import cv2
import time

import modules.shared_data as shared

from modules.camera_thread import CameraThread
from modules.gps_thread import GPSThread

from modules.lane_detection import (
    detect_lane_lines
)

from modules.lane_departure import (
    check_lane_departure
)

camera_thread = CameraThread()
gps_thread = GPSThread()

camera_thread.start()
gps_thread.start()

while True:

    if shared.frame is None:
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

    cv2.putText(
        frame,
        f"LDW:{lane_status}",
        (20,40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0,255,255),
        2
    )

    cv2.putText(
        frame,
        f"SPEED:{shared.gps_speed:.1f}",
        (20,80),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255,255,0),
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

    cv2.imshow(
        "LDW",
        frame
    )

    if cv2.waitKey(1)==ord("q"):
        break