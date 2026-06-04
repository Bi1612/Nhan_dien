import threading
import serial
import time

import modules.shared_data as shared

class SensorThread(threading.Thread):

    def __init__(self):

        super().__init__()

        self.daemon = True

        self.ser = serial.Serial(
            "/dev/ttyACM0",
            115200,
            timeout=1
        )

    def run(self):

        while shared.running:

            try:

                line = self.ser.readline()

                line = line.decode().strip()

                data = line.split(",")

                if len(data) != 4:
                    continue

                distance = float(data[0])

                ax = float(data[1])

                ay = float(data[2])

                az = float(data[3])

                shared.distance = distance

                shared.ax = ax

                shared.ay = ay

                shared.az = az

            except:

                pass

            time.sleep(0.01)

    def stop(self):

        self.ser.close()