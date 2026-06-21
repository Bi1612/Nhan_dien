# ==========================================================
# File      : audio_alert.py
# Function  : Blind Assistive Audio Warning System (Optimized)
# ==========================================================

import os
import threading
import queue
import time

# Hàng đợi quản lý câu lệnh thoại, tránh việc các âm thanh đè lên nhau
audio_queue = queue.Queue()

def _audio_worker():
    """Luồng nền xử lý phát âm thanh tuần tự - Đã tối ưu chống chiếm dụng CPU"""
    while True:
        # Nếu hàng đợi trống, luồng sẽ tạm nghỉ một chút để tránh nuốt băng thông CPU
        if audio_queue.empty():
            time.sleep(0.05)
            continue
            
        item = audio_queue.get()
        if item is None:
            break
        
        try:
            # Nếu là chuỗi ký tự text -> Sử dụng espeak để đọc chữ thành tiếng (TTS)
            if isinstance(item, str) and not item.endswith(".wav"):
                # -v vi+f2: Chọn giọng tiếng Việt pha giọng nữ để nghe dễ chịu hơn
                # -s 140: Giảm tốc độ nói xuống một chút để người mù nghe rõ ràng hơn
                # -p 45: Chỉnh tông giọng trầm ấm hơn
                os.system(f"espeak -v vi+f2 -s 140 -p 45 \"{item}\"")
            
            # Nếu truyền vào đường dẫn file .wav -> Dùng aplay phát âm thanh trực tiếp
            elif isinstance(item, str) and item.endswith(".wav"):
                if os.path.exists(item):
                    os.system(f"aplay {item}")
                else:
                    print(f"[Audio Error] Không tìm thấy file âm thanh: {item}")
        except Exception as e:
            print(f"[Audio Error] Lỗi phát âm thanh: {e}")
            
        audio_queue.task_done()
        time.sleep(0.1)

# Khởi chạy luồng âm thanh chạy ngầm ngay khi import module
worker_thread = threading.Thread(target=_audio_worker, daemon=True)
worker_thread.start()

def play_voice_alert(message):
    """
    Hàm đẩy câu lệnh hoặc file âm thanh vào hàng đợi để phát cho người mù.
    Giới hạn hàng đợi không quá 2 câu lệnh để tránh bị trễ thông tin thời gian thực (Real-time).
    """
    if audio_queue.qsize() < 2:
        audio_queue.put(message)
