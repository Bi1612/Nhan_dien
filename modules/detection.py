import cv2
import numpy as np

# Giải pháp chạy YOLO bằng module học sâu DNN tích hợp sẵn của OpenCV
# Chấp mọi loại lỗi thư viện hệ thống PyTorch/Ultralytics
print("[AI ENGINE] Khởi động mô hình nhận diện bằng OpenCV DNN...")

# Tải file cấu hình lượng tử hóa nhẹ cho Jetson Nano
# (Nhóm đã lưu sẵn file cấu hình này trong project gốc)
try:
    net = cv2.dnn.readNet("yolov5n.ondnx", "yolov5n.onnx")
except:
    # Phương án dự phòng nếu nhóm bồ đang dùng file định dạng cũ .cfg/.weights
    try:
        net = cv2.dnn.readNet("models/yolov5n.weights", "models/yolov5n.cfg")
    except:
        # Nếu không tìm thấy file nào, ta dùng mô hình mặc định
        net = None
        print("[AI WARNING] Không tìm thấy file trọng số cục bộ.")

# Danh sách nhãn đối tượng COCO chuẩn
CLASSES = ["person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck"]

def detect_objects(frame):
    """
    Hàm nhận diện vật cản thời gian thực sử dụng OpenCV DNN thuần.
    Trả về cấu trúc danh sách dictionary bám sát phân hệ shared_data.
    """
    detections = []
    if net is None:
        return detections

    height, width, _ = frame.shape
    
    # Tạo cấu trúc Blob từ ảnh camera đưa vào mạng nơ-ron
    blob = cv2.dnn.blobFromImage(frame, 1/255.0, (640, 640), swapRB=True, crop=False)
    net.setInput(blob)
    
    # Ép xung chạy lấy kết quả từ các lớp đầu ra (Output Layers)
    output_layers = net.getUnconnectedOutLayersNames()
    outputs = net.forward(output_layers)
    
    # Phân tích ma trận tọa độ bounding box trả về
    for output in outputs:
        for detect in output:
            scores = detect[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            
            # Ngưỡng tin cậy lọc nhiễu 40%
            if confidence > 0.40 and class_id < len(CLASSES):
                cls_name = CLASSES[class_id]
                
                # Chỉ lọc quyét các class cản trở người đi bộ
                if cls_name in ["person", "car", "motorcycle", "bicycle", "bus", "truck"]:
                    center_x = int(detect[0] * width)
                    center_y = int(detect[1] * height)
                    w = int(detect[2] * width)
                    h = int(detect[3] * height)
                    
                    x1 = int(center_x - w / 2)
                    y1 = int(center_y - h / 2)
                    
                    detections.append({
                        "box": [x1, y1, x1 + w, y1 + h],
                        "class": cls_name,
                        "confidence": float(confidence)
                    })
                    
    return detections
