# ==========================================================
# File      : sensor_thread.py
# Function  : Sensor fusion thread
# ==========================================================

import threading
import time

import modules.shared_data as shared

from modules.ultrasonic import read_ultrasonic
from modules.imu_module import read_imu

# ==========================================================
# Sensor thread
# ==========================================================

class SensorThread(threading.Thread):

    def __init__(self):

        threading.Thread.__init__(self)

        self.daemon = True

    def run(self):

        while shared.running:

            shared.sensor_distance = (
                read_ultrasonic()
            )

            shared.ax, shared.ay, shared.az = (
                read_imu()
            )

            time.sleep(0.05)