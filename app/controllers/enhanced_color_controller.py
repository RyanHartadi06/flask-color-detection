import time
import cv2
import numpy as np
from flask import Response, jsonify
from app.services.enhanced_color_service import (
    generate_video_stream, camera, camera_lock, reconnect_camera,
    enhanced_color_preprocessing, adaptive_pink_detection, 
    adaptive_white_detection, analyze_color_distribution,
    last_frame, last_frame_time
)

class EnhancedColorController:

    @staticmethod
    def calculate_enhanced_color_percentage(frame):
        """
        Enhanced color percentage calculation dengan adaptive detection
        """
        try:
            h, w, _ = frame.shape
            box_size = 200
            top_left_x = w // 2 - box_size // 2
            top_left_y = h // 2 - box_size // 2
            bottom_right_x = top_left_x + box_size
            bottom_right_y = top_left_y + box_size

            roi = frame[top_left_y:bottom_right_y, top_left_x:bottom_right_x]
            
            # Enhanced preprocessing
            enhanced_roi = enhanced_color_preprocessing(roi)
            
            # Convert to HSV
            hsv = cv2.cvtColor(enhanced_roi, cv2.COLOR_BGR2HSV)
            original_hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
            
            # Adaptive detection
            pink_mask = adaptive_pink_detection(hsv, roi)
            white_mask = adaptive_white_detection(original_hsv, roi)
            
            # Calculate percentages
            total_pixels = roi.shape[0] * roi.shape[1]
            pink_pixels = cv2.countNonZero(pink_mask)
            white_pixels = cv2.countNonZero(white_mask)

            pink_percent = round((pink_pixels / total_pixels) * 100, 2)
            white_percent = round((white_pixels / total_pixels) * 100, 2)
            
            # Get color analysis for debugging
            color_analysis = analyze_color_distribution(roi)

            return pink_percent, white_percent, color_analysis
            
        except Exception as e:
            print(f"❌ Error calculating enhanced color percentage: {e}")
            return 0.0, 0.0, {}

    @staticmethod
    def generate_video_stream():
        """Use the enhanced video stream"""
        try:
            yield from generate_video_stream()
        except Exception as e:
            print(f"❌ Error in enhanced video stream: {e}")
            # Return error frame
            error_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(error_frame, 'ENHANCED STREAM ERROR', (150, 240),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            ret, buffer = cv2.imencode('.jpg', error_frame)
            if ret:
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    @staticmethod
    def detect_color():
        """Enhanced color detection dengan debugging info menggunakan cached frame"""
        global last_frame, last_frame_time
        
        try:
            # Get cached frame from video stream
            with camera_lock:
                current_time = time.time()
                
                # Check if we have a recent frame (within 5 seconds)
                if last_frame is not None and (current_time - last_frame_time) < 5:
                    frame = last_frame.copy()
                else:
                    # Try to get new frame if cache is stale
                    if camera is None or not camera.isOpened():
                        print("⚠️ Camera tidak tersedia di enhanced detect_color(), mencoba reconnect...")
                        if not reconnect_camera():
                            return jsonify({
                                'error': 'Camera not available',
                                'pink': 0, 
                                'white': 0,
                                'status': 'disconnected',
                                'debug_info': {}
                            })

                    # Try to read frame with minimal blocking
                    success, new_frame = camera.read()
                    if success and new_frame is not None:
                        last_frame = new_frame.copy()
                        last_frame_time = current_time
                        frame = new_frame
                    elif last_frame is not None:
                        # Use stale frame if available
                        frame = last_frame.copy()
                        print("⚠️ Using cached frame due to read failure")
                    else:
                        print("⚠️ Gagal membaca frame di enhanced detect_color()")
                        return jsonify({
                            'error': 'Failed to read frame',
                            'pink': 0, 
                            'white': 0,
                            'status': 'no_frame',
                            'debug_info': {}
                        })

            pink_percent, white_percent, color_analysis = EnhancedColorController.calculate_enhanced_color_percentage(frame)
            
            return jsonify({
                'pink': float(pink_percent), 
                'white': float(white_percent),
                'status': 'success',
                'debug_info': {
                    'dominant_hue': int(color_analysis.get('dominant_hue', 0)),
                    'avg_saturation': float(round(color_analysis.get('avg_saturation', 0), 1)),
                    'avg_value': float(round(color_analysis.get('avg_value', 0), 1)),
                    'detection_method': 'enhanced_adaptive',
                    'active_ranges': 4,
                    'preprocessing': {
                        'histogram_eq': True,
                        'gamma_correction': True,
                        'saturation_boost': True
                    },
                    'frame_age': current_time - last_frame_time if last_frame_time > 0 else -1
                }
            })
            
        except cv2.error as e:
            print(f"❌ OpenCV Error in enhanced detect_color(): {e}")
            return jsonify({
                'error': f'OpenCV Error: {str(e)}',
                'pink': 0, 
                'white': 0,
                'status': 'opencv_error',
                'debug_info': {}
            })
            
        except Exception as e:
            print(f"❌ Unexpected error in enhanced detect_color(): {e}")
            return jsonify({
                'error': f'Unexpected error: {str(e)}',
                'pink': 0, 
                'white': 0,
                'status': 'unexpected_error',
                'debug_info': {}
            })
