import threading
import modules.shared_data as shared

class SensorThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True

    def run(self):
        import time 
        
        print("[SENSOR INFO] Kích hoạt luồng giả lập cảm biến siêu nhẹ...")
        
        # Ép trạng thái nút bấm mặc định hoặc khoảng cách an toàn ban đầu
        shared.distance = 100.0  # Mặc định khoảng cách an toàn là 100cm
        
        # Giả lập trạng thái nút bấm Mượn/Trả sách cho đồ án (nếu cần)
        # Giả sử nút bấm chưa được nhấn (0 là chưa nhấn, 1 là nhấn)
        if not hasattr(shared, 'borrow_pressed'):
            shared.borrow_pressed = 0
        if not hasattr(shared, 'return_pressed'):
            shared.return_pressed = 0

        while shared.running:
            try:
                # 🌟 GIẢ LẬP DỮ LIỆU ĐỂ GIẢI PHÓNG HỆ THỐNG
                # Cứ mỗi vòng lặp, ta giữ nguyên khoảng cách an toàn 
                shared.distance = 100.0
                
                # Biến này giúp giả lập dữ liệu liên tục mà CPU không bị chạy quá tải
                # Tăng thời gian ngủ lên 0.2 giây để Jetson Nano thở, cực kỳ nhẹ máy!
                time.sleep(0.2)
                
            except Exception:
                time.sleep(0.5)
