import time
import cv2
import numpy as np
from flask import Response, jsonify
from app.services.color_service import generate_video_stream, camera, camera_lock, reconnect_camera

class ColorController:

    @staticmethod
    def calculate_color_percentage(frame):
        try:
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
        except Exception as e:
            print(f"❌ Error calculating color percentage: {e}")
            return 0.0, 0.0

    @staticmethod
    def generate_video_stream():
        """Use the improved video stream from color_service"""
        try:
            yield from generate_video_stream()
        except Exception as e:
            print(f"❌ Error in video stream: {e}")
            # Return error frame
            error_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(error_frame, 'STREAM ERROR', (200, 240),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            ret, buffer = cv2.imencode('.jpg', error_frame)
            if ret:
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    @staticmethod
    def detect_color():
        global camera
        
        try:
            # Check if camera is available
            if camera is None or not camera.isOpened():
                print("⚠️ Camera tidak tersedia di detect_color(), mencoba reconnect...")
                if not reconnect_camera():
                    return jsonify({
                        'error': 'Camera not available',
                        'pink': 0, 
                        'white': 0,
                        'status': 'disconnected'
                    })

            # Try to read frame with timeout protection
            with camera_lock:
                success, frame = camera.read()
                
            if not success or frame is None:
                print("⚠️ Gagal membaca frame di detect_color()")
                # Don't immediately reconnect, let the video stream handle it
                return jsonify({
                    'error': 'Failed to read frame',
                    'pink': 0, 
                    'white': 0,
                    'status': 'no_frame'
                })

            pink_percent, white_percent = ColorController.calculate_color_percentage(frame)
            return jsonify({
                'pink': pink_percent, 
                'white': white_percent,
                'status': 'success'
            })
            
        except cv2.error as e:
            print(f"❌ OpenCV Error in detect_color(): {e}")
            return jsonify({
                'error': f'OpenCV Error: {str(e)}',
                'pink': 0, 
                'white': 0,
                'status': 'opencv_error'
            })
            
        except Exception as e:
            print(f"❌ Unexpected error in detect_color(): {e}")
            return jsonify({
                'error': f'Unexpected error: {str(e)}',
                'pink': 0, 
                'white': 0,
                'status': 'unexpected_error'
            })