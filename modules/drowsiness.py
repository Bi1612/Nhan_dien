# ==========================================================
# File      : drowsiness.py
# Function  : Driver drowsiness detection
# ==========================================================

import cv2
import dlib
import numpy as np

# ==========================================================
# Face detector
# ==========================================================

detector = dlib.get_frontal_face_detector()

predictor = dlib.shape_predictor(
    "models/shape_predictor_68_face_landmarks.dat"
)

# ==========================================================
# Eye aspect ratio
# ==========================================================

def eye_aspect_ratio(eye):

    A = np.linalg.norm(eye[1] - eye[5])

    B = np.linalg.norm(eye[2] - eye[4])

    C = np.linalg.norm(eye[0] - eye[3])

    ear = (A + B) / (2.0 * C)

    return ear

# ==========================================================
# Detect drowsiness
# ==========================================================

def detect_drowsiness(frame):

    gray = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2GRAY
    )

    faces = detector(gray)

    if len(faces) == 0:
        return "NO FACE"

    for face in faces:

        landmarks = predictor(
            gray,
            face
        )

        left_eye = []

        for n in range(36, 42):

            x = landmarks.part(n).x
            y = landmarks.part(n).y

            left_eye.append([x, y])

        left_eye = np.array(
            left_eye,
            dtype=np.float32
        )

        ear = eye_aspect_ratio(
            left_eye
        )

        if ear < 0.20:
            return "DROWSY"

        return "AWAKE"

    return "UNKNOWN"