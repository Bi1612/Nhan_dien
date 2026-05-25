import cv2

def draw_dashboard(
    frame,
    fps,
    latency,
    car_count,
    person_count,
    warning,
    fcw_text,
    nearest_distance,
    speed_kmh,
    speed_status,
    latitude,
    longitude,
    sign_type
):

    cv2.rectangle(frame, (0, 0), (300, 320), (0, 0, 0), -1)

    cv2.putText(
        frame,
        f"FPS: {fps:.1f}",
        (20, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 0),
        2
    )

    cv2.putText(
        frame,
        f"Latency: {latency:.1f} ms",
        (20, 60),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 0),
        2
    )

    cv2.putText(
        frame,
        f"Cars: {car_count}",
        (20, 100),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 0, 0),
        2
    )

    cv2.putText(
        frame,
        f"Persons: {person_count}",
        (20, 130),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 0, 255),
        2
    )

    cv2.putText(
        frame,
        warning,
        (20, 180),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 255),
        2
    )

    cv2.putText(
        frame,
        fcw_text,
        (20, 220),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 0, 255),
        2
    )

    cv2.putText(
        frame,
        f"Distance: {nearest_distance:.1f}m",
        (20, 260),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )

    cv2.putText(
    frame,
    f"Speed: {speed_kmh:.1f} km/h",
    (20, 300),
    cv2.FONT_HERSHEY_SIMPLEX,
    0.7,
    (255, 255, 0),
    2
    )

    cv2.putText(
        frame,
        f"GPS: {latitude:.4f}",
        (20, 340),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (255, 255, 255),
        1
    )

    cv2.putText(
        frame,
        f"{longitude:.4f}",
        (20, 360),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (255, 255, 255),
        1
    )

    cv2.putText(
        frame,
        f"Traffic Sign: {sign_type}",
        (20, 400),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 0, 255),
        2
    )