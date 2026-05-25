# ==========================================================
# File      : gps_module.py
# Function  : GPS reader and overspeed warning system
# Author    : Group 4
# Target    : NVIDIA Jetson Nano
# ==========================================================

import serial
import pynmea2

# ==========================================================
# Initialize GPS serial port
# ==========================================================

gps_serial = serial.Serial(
    "/dev/ttyUSB0",
    baudrate=9600,
    timeout=1
)

# ==========================================================
# Function : read_gps
# Purpose  : Read GPS coordinates and speed
# Input    : None
# Output   : latitude, longitude, speed_kmh
# Notes    : Uses NMEA parser
# ==========================================================

def read_gps():

    latitude = 0.0
    longitude = 0.0
    speed_kmh = 0.0

    try:

        line = gps_serial.readline().decode(
            'ascii',
            errors='replace'
        )

        if line.startswith('$GPRMC'):

            msg = pynmea2.parse(line)

            latitude = msg.latitude
            longitude = msg.longitude

            # Convert knots to km/h
            speed_kmh = float(msg.spd_over_grnd) * 1.852

    except:
        pass

    return latitude, longitude, speed_kmh