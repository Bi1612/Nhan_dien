import serial
import pynmea2
import time

PORT = '/dev/ttyUSB0' # Sửa lại nếu cổng của Bi hiện tên khác
BAUD = 9600

print("--- ĐANG QUÉT DỮ LIỆU GPS NEO-6M ---")
print("Lưu ý: Nếu ở trong nhà, hệ thống sẽ hiển thị 'Đang dò sóng...'")

try:
    ser = serial.Serial(PORT, baudrate=BAUD, timeout=1)
    while True:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8', errors='ignore')
            if line.startswith('$GPRMC'):
                try:
                    msg = pynmea2.parse(line)
                    if msg.status == 'A':
                        speed_kph = msg.spd_over_grnd * 1.852 if msg.spd_over_grnd else 0.0
                        print(f"[OK] Vĩ độ (Lat): {msg.latitude} | Kinh độ (Lon): {msg.longitude} | Vận tốc: {speed_kph:.2f} km/h")
                    else:
                        print("[SEARCHING] Đang đợi khóa tín hiệu vệ tinh (Đèn LED đỏ trên GPS chưa nháy)...")
                except pynmea2.ParseError:
                    continue
        time.sleep(0.5)
except KeyboardInterrupt:
    print("\nDừng test.")
except Exception as e:
    print(f"Lỗi kết nối: {e}")
