import serial
import pynmea2

from config import *

gps_serial = serial.Serial(
    GPS_PORT,
    GPS_BAUDRATE,
    timeout=1
)

def read_gps():

    try:

        line = gps_serial.readline()

        line = line.decode(
            "utf-8",
            errors="ignore"
        )

        if "$GPRMC" in line:

            msg = pynmea2.parse(line)

            latitude = msg.latitude

            longitude = msg.longitude

            speed_kmh = (
                float(msg.spd_over_grnd)
                * 1.852
            )

            return (
                latitude,
                longitude,
                speed_kmh
            )

    except:
        pass

    return (
        0.0,
        0.0,
        0.0
    )