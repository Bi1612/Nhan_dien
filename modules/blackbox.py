import cv2
from datetime import datetime

video_writer = None

def start_recording():

    global video_writer

    filename = datetime.now().strftime(
        "recordings/%Y%m%d_%H%M%S.avi"
    )

    fourcc = cv2.VideoWriter_fourcc(*'XVID')

    video_writer = cv2.VideoWriter(
        filename,
        fourcc,
        20.0,
        (416, 416)
    )

def write_frame(frame):

    global video_writer

    if video_writer is not None:
        video_writer.write(frame)

def stop_recording():

    global video_writer

    if video_writer is not None:
        video_writer.release()

def log_gps(latitude, longitude, speed):

    with open("logs/gps_log.csv", "a") as f:

        f.write(
            f"{latitude},{longitude},{speed}\n"
        )