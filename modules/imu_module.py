# ==========================================================
# File      : imu_module.py
# Function  : MPU6050 sensor reader
# ==========================================================

import serial

ser = serial.Serial(
    '/dev/ttyUSB0',
    115200,
    timeout=1
)

# ==========================================================
# Read acceleration data
# ==========================================================

def read_imu():

    try:

        line = ser.readline().decode().strip()

        values = line.split(',')

        ax = int(values[1])
        ay = int(values[2])
        az = int(values[3])

        return ax, ay, az

    except:
        return 0, 0, 0