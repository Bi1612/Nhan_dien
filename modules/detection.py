from yoloDet import YoloTRT

from config import *

model = YoloTRT(
    library="yolov5/build_1/libmyplugins.so",
    engine="yolov5/build_1/yolov5n.engine",
    conf=CONFIDENCE_THRESHOLD,
    yolo_ver="v5"
)

def detect_objects(frame):

    detections, t = model.Inference(
        frame
    )

    return detections