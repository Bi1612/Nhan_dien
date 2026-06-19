# ==========================================================
# File      : audio_alert.py
# Function  : Blind Assistive Audio Warning System
# ==========================================================

import os
import threading
import queue
import time

# Hàng đợi quản lý câu lệnh thoại, tránh việc các âm thanh đè lên nhau
audio_queue = queue.Queue()

def _audio_worker():
    """Luồng nền xử lý phát âm thanh tuần tự"""
    while True:
        item = audio_queue.get()
        if item is None:
            break
        
        # Nếu là chuỗi ký tự text -> Sử dụng espeak để đọc (TTS)
        if isinstance(item, str) and not item.endswith(".wav"):
            # espeak -v vi: Chọn giọng tiếng Việt (nếu có), -s 150: tốc độ nói
            os.system(f"espeak -v vi -s 150 \"{item}\"")
        
        # Nếu truyền vào đường dẫn file .wav -> Dùng aplay phát âm thanh (Không dùng & để chờ đọc xong)
        elif isinstance(item, str) and item.endswith(".wav"):
            os.system(f"aplay {item}")
            
        audio_queue.task_done()
        time.sleep(0.1)

# Khởi chạy luồng âm thanh chạy ngầm ngay khi import module
worker_thread = threading.Thread(target=_audio_worker, daemon=True)
worker_thread.start()

def play_voice_alert(message):
    """
    Hàm đẩy câu lệnh hoặc file âm thanh vào hàng đợi để phát cho người mù
    Ví dụ: play_voice_alert("Phat hien vat can co dinh") hoặc play_voice_alert("sounds/left.wav")
    """
    # Giới hạn hàng đợi không quá 3 câu lệnh để tránh bị trễ thông tin thời gian thực
    if audio_queue.qsize() < 3:
        audio_queue.put(message)
