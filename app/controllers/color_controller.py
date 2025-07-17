import cv2
import numpy as np
from flask import Response, jsonify

# Global kamera supaya tidak buka-tutup
camera = cv2.VideoCapture(0)

class ColorController:

    @staticmethod
    def calculate_color_percentage(frame):
        h, w, _ = frame.shape
        box_size = 200
        top_left_x = w // 2 - box_size // 2
        top_left_y = h // 2 - box_size // 2
        bottom_right_x = top_left_x + box_size
        bottom_right_y = top_left_y + box_size

        roi = frame[top_left_y:bottom_right_y, top_left_x:bottom_right_x]
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

        lower_pink = np.array([140, 50, 50])
        upper_pink = np.array([170, 255, 255])
        pink_mask = cv2.inRange(hsv, lower_pink, upper_pink)

        lower_white = np.array([0, 0, 200])
        upper_white = np.array([180, 50, 255])
        white_mask = cv2.inRange(hsv, lower_white, upper_white)

        total_pixels = roi.shape[0] * roi.shape[1]
        pink_pixels = cv2.countNonZero(pink_mask)
        white_pixels = cv2.countNonZero(white_mask)

        pink_percent = round((pink_pixels / total_pixels) * 100, 2)
        white_percent = round((white_pixels / total_pixels) * 100, 2)

        return pink_percent, white_percent

    @staticmethod
    def generate_video_stream():
        while True:
            success, frame = camera.read()
            if not success:
                break

            pink_percent, white_percent = ColorController.calculate_color_percentage(frame)

            # Gambarkan kotak tengah
            h, w, _ = frame.shape
            box_size = 200
            top_left_x = w // 2 - box_size // 2
            top_left_y = h // 2 - box_size // 2
            bottom_right_x = top_left_x + box_size
            bottom_right_y = top_left_y + box_size

            cv2.rectangle(frame, (top_left_x, top_left_y), (bottom_right_x, bottom_right_y), (0, 255, 0), 2)

            cv2.putText(frame, f'Pink: {pink_percent}%', (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2)
            cv2.putText(frame, f'White: {white_percent}%', (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()

            yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    @staticmethod
    def detect_color():
        success, frame = camera.read()
        if not success:
            return jsonify({'pink': 0, 'white': 0})

        pink_percent, white_percent = ColorController.calculate_color_percentage(frame)
        return jsonify({'pink': pink_percent, 'white': white_percent})
