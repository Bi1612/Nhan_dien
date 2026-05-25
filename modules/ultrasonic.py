# ==========================================================
# File      : ultrasonic.py
# Function  : HC-SR04 sensor reader
# ==========================================================

import serial

ser = serial.Serial(
    '/dev/ttyUSB0',
    115200,
    timeout=1
)

# ==========================================================
# Read ultrasonic distance
# ==========================================================

def read_ultrasonic():

    try:

        line = ser.readline().decode().strip()

        values = line.split(',')

        distance = float(values[0])

        return distance

    except:
        return 999.0