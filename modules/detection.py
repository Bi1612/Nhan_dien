import cv2
import numpy as np
import os

# Giải pháp chạy YOLO bằng module học sâu DNN tích hợp sẵn của OpenCV
print("[AI ENGINE] Khởi động mô hình nhận diện bằng OpenCV DNN...")

# Định nghĩa đường dẫn file yolov5n.onnx nằm ngay trong thư mục modules
model_path = os.path.join(os.path.dirname(__file__), "yolov5n.onnx")

# Kiểm tra file cục bộ để nạp trực tiếp, không chạy vòng vèo
if os.path.exists(model_path):
    # SỬA LỖI: Đọc file ONNX chuẩn với 1 tham số duy nhất
    net = cv2.dnn.readNet(model_path)
    
    # 🚀 KÍCH HOẠT NHÂN ĐỒ HỌA CUDA CHO JETSON NANO (Giúp khởi động và chạy siêu nhanh)
    net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
    net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)
    
    print(f"[AI INFO] Đã nạp thành công mô hình bằng CUDA: {model_path}")
else:
    net = None
    print("[AI WARNING] Không tìm thấy file yolov5n.onnx cục bộ trong thư mục modules!")

# Danh sách nhãn đối tượng COCO chuẩn
CLASSES = ["person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck"]

def detect_objects(frame):
    """
    Hàm nhận diện vật cản thời gian thực sử dụng OpenCV DNN thuần.
    """
    detections = []
    if net is None:
        return detections

    height, width, _ = frame.shape
    
    # Tạo cấu trúc Blob từ ảnh camera đưa vào mạng nơ-ron
    blob = cv2.dnn.blobFromImage(frame, 1/255.0, (640, 640), swapRB=True, crop=False)
    net.setInput(blob)
    
    # Lấy kết quả từ các lớp đầu ra
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
                
                # Chỉ lọc quét các class cản trở người đi bộ
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