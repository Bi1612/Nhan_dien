import threading
import time

import modules.shared_data as shared

class GPSThread(threading.Thread):

    def __init__(self):

        threading.Thread.__init__(self)

        self.daemon = True

    def run(self):

        while shared.running:

            # Fake speed

            shared.gps_speed = 35.0

            time.sleep(1)