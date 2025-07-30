#!/usr/bin/env python3
"""
Enhanced Color Detection Service dengan Adaptive Color Range
Mengatasi masalah deteksi pink yang terlihat abu-abu
"""

import cv2
import numpy as np
import time
import threading
import sys
import os

# Try to import config, fallback to default values if not available
try:
    # Add config directory to path
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from config.camera_config import CameraConfig
    print("✅ Config loaded successfully")
except ImportError as e:
    print(f"⚠️ Config import failed, using defaults: {e}")
    # Fallback configuration
    class CameraConfig:
        RTSP_URL = 'rtsp://admin:Petro%402025@10.14.66.163:554/Streaming/Channels/102?transportmode=unicast'
        TARGET_WIDTH = 1280
        TARGET_HEIGHT = 720
        MAX_DISPLAY_WIDTH = 1024
        MAX_DISPLAY_HEIGHT = 768
        TARGET_FPS = 15
        BUFFER_SIZE = 1
        OPEN_TIMEOUT = 5000
        READ_TIMEOUT = 5000
        DETECTION_BOX_SIZE = 200
        JPEG_QUALITY = 85
        
        @classmethod
        def get_optimal_resolution(cls):
            return (cls.TARGET_WIDTH, cls.TARGET_HEIGHT)
        
        @classmethod
        def get_display_limits(cls):
            return (cls.MAX_DISPLAY_WIDTH, cls.MAX_DISPLAY_HEIGHT)
        
        @classmethod
        def should_scale_frame(cls, frame_width, frame_height):
            return (frame_width > cls.MAX_DISPLAY_WIDTH or 
                    frame_height > cls.MAX_DISPLAY_HEIGHT)
        
        @classmethod
        def calculate_scale_factor(cls, frame_width, frame_height):
            scale_w = cls.MAX_DISPLAY_WIDTH / frame_width
            scale_h = cls.MAX_DISPLAY_HEIGHT / frame_height
            return min(scale_w, scale_h)

# RTSP URL dari konfigurasi
rtsp_url = CameraConfig.RTSP_URL
camera = None
camera_lock = threading.Lock()
reconnect_attempts = 0
max_reconnect_attempts = 5
base_reconnect_delay = 1
last_frame = None  # Cache last successful frame
last_frame_time = 0

def init_camera():
    global camera
    try:
        if camera:
            camera.release()
        camera = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
        camera.set(cv2.CAP_PROP_BUFFERSIZE, CameraConfig.BUFFER_SIZE)
        camera.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, CameraConfig.OPEN_TIMEOUT)
        camera.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, CameraConfig.READ_TIMEOUT)
        
        # Set resolution dari konfigurasi untuk mengurangi zoom
        target_width, target_height = CameraConfig.get_optimal_resolution()
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, target_width)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, target_height)
        
        # Set FPS dari konfigurasi untuk stabilitas
        camera.set(cv2.CAP_PROP_FPS, CameraConfig.TARGET_FPS)
        
        if not camera.isOpened():
            print("❌ Tidak bisa membuka RTSP stream")
            return False
        
        ret, test_frame = camera.read()
        if not ret or test_frame is None:
            print("❌ Tidak bisa membaca frame test")
            camera.release()
            camera = None
            return False
            
        print(f"✅ Berhasil koneksi ke RTSP stream - Resolution: {test_frame.shape[1]}x{test_frame.shape[0]}")
        return True
    except Exception as e:
        print(f"❌ Gagal init camera: {e}")
        if camera:
            camera.release()
            camera = None
        return False

def reconnect_camera():
    global camera, reconnect_attempts
    
    with camera_lock:
        if reconnect_attempts >= max_reconnect_attempts:
            print(f"❌ Max reconnect attempts ({max_reconnect_attempts}) reached")
            return False
            
        reconnect_attempts += 1
        delay = min(base_reconnect_delay * (2 ** (reconnect_attempts - 1)), 30)
        
        print(f"🔁 Reconnect attempt {reconnect_attempts}/{max_reconnect_attempts} after {delay}s delay...")
        time.sleep(delay)
        
        try:
            if camera:
                camera.release()
                camera = None
                time.sleep(0.5)
            
            return init_camera()
            
        except Exception as e:
            print(f"❌ Gagal reconnect: {e}")
            return False

def reset_reconnect_counter():
    global reconnect_attempts
    reconnect_attempts = 0

def enhanced_color_preprocessing(roi):
    """
    Preprocessing untuk meningkatkan deteksi warna pink yang terlihat abu-abu
    """
    # 1. Histogram Equalization untuk normalisasi brightness
    lab = cv2.cvtColor(roi, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    l = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8)).apply(l)
    enhanced_lab = cv2.merge([l, a, b])
    enhanced_bgr = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
    
    # 2. Gamma correction untuk brightening
    gamma = 1.2
    gamma_corrected = np.power(enhanced_bgr / 255.0, 1/gamma) * 255.0
    gamma_corrected = gamma_corrected.astype(np.uint8)
    
    # 3. Saturation boost untuk meningkatkan warna
    hsv_boost = cv2.cvtColor(gamma_corrected, cv2.COLOR_BGR2HSV)
    hsv_boost[:, :, 1] = cv2.multiply(hsv_boost[:, :, 1], 1.3)  # Boost saturation
    enhanced_final = cv2.cvtColor(hsv_boost, cv2.COLOR_HSV2BGR)
    
    return enhanced_final

def adaptive_pink_detection(hsv_roi, original_roi):
    """
    Deteksi pink dengan multiple range dan adaptive thresholding
    """
    # Multiple pink ranges untuk menangkap variasi pink
    pink_ranges = [
        # Range 1: Pink terang
        ([140, 40, 40], [170, 255, 255]),
        # Range 2: Pink pucat/muda
        ([130, 20, 100], [180, 180, 255]),
        # Range 3: Pink keabu-abuan (yang terlihat abu-abu tapi sebenarnya pink)
        ([120, 15, 80], [180, 100, 220]),
        # Range 4: Pink dalam kondisi cahaya redup
        ([135, 30, 50], [175, 200, 200])
    ]
    
    combined_mask = np.zeros(hsv_roi.shape[:2], dtype=np.uint8)
    
    for lower, upper in pink_ranges:
        lower_np = np.array(lower)
        upper_np = np.array(upper)
        mask = cv2.inRange(hsv_roi, lower_np, upper_np)
        combined_mask = cv2.bitwise_or(combined_mask, mask)
    
    # Morphological operations untuk cleanup
    kernel = np.ones((3,3), np.uint8)
    combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel)
    combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel)
    
    return combined_mask

def adaptive_white_detection(hsv_roi, original_roi):
    """
    Deteksi white dengan adaptive brightness threshold
    """
    # Hitung rata-rata brightness dari ROI
    gray_roi = cv2.cvtColor(original_roi, cv2.COLOR_BGR2GRAY)
    avg_brightness = np.mean(gray_roi)
    
    # Adaptive threshold berdasarkan kondisi pencahayaan
    if avg_brightness > 150:  # Kondisi terang
        lower_white = np.array([0, 0, 180])
        upper_white = np.array([180, 40, 255])
    elif avg_brightness > 100:  # Kondisi normal
        lower_white = np.array([0, 0, 140])
        upper_white = np.array([180, 60, 255])
    else:  # Kondisi redup
        lower_white = np.array([0, 0, 100])
        upper_white = np.array([180, 80, 255])
    
    white_mask = cv2.inRange(hsv_roi, lower_white, upper_white)
    
    # Cleanup
    kernel = np.ones((3,3), np.uint8)
    white_mask = cv2.morphologyEx(white_mask, cv2.MORPH_CLOSE, kernel)
    
    return white_mask

def analyze_color_distribution(roi):
    """
    Analisis distribusi warna untuk debugging
    """
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    
    # Hitung histogram untuk setiap channel HSV
    h_hist = cv2.calcHist([hsv], [0], None, [180], [0, 180])
    s_hist = cv2.calcHist([hsv], [1], None, [256], [0, 256])
    v_hist = cv2.calcHist([hsv], [2], None, [256], [0, 256])
    
    # Temukan peak values
    h_peak = np.argmax(h_hist)
    s_peak = np.argmax(s_hist)
    v_peak = np.argmax(v_hist)
    
    return {
        'dominant_hue': h_peak,
        'dominant_saturation': s_peak,
        'dominant_value': v_peak,
        'avg_saturation': np.mean(hsv[:, :, 1]),
        'avg_value': np.mean(hsv[:, :, 2])
    }

# Initialize camera
if not init_camera():
    print("⚠️ Gagal initial connection, akan mencoba reconnect saat streaming dimulai")

def generate_video_stream():
    global camera
    
    print("🎥 Starting enhanced video stream generator...")
    
    # Initialize camera if not already done
    if camera is None:
        print("📷 Camera not initialized, initializing now...")
        if not init_camera():
            print("❌ Failed to initialize camera")
            error_frame = create_error_frame("Camera initialization failed")
            ret, buffer = cv2.imencode('.jpg', error_frame)
            if ret:
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            return
    
    consecutive_failures = 0
    max_consecutive_failures = 10
    frame_count = 0
    
    while True:
        try:
            frame_count += 1
            
            # Check if camera is available
            if camera is None or not camera.isOpened():
                print(f"⚠️ Frame {frame_count}: Camera tidak tersedia, mencoba reconnect...")
                if not reconnect_camera():
                    print(f"❌ Frame {frame_count}: Reconnect failed")
                    error_frame = create_error_frame("Camera disconnected")
                    ret, buffer = cv2.imencode('.jpg', error_frame)
                    if ret:
                        frame_bytes = buffer.tobytes()
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                    time.sleep(1)
                    continue
            
            # Read frame with timeout protection
            with camera_lock:
                ret, frame = camera.read()
            
            if not ret or frame is None:
                consecutive_failures += 1
                print(f"⚠️ Frame {frame_count}: Gagal membaca frame ({consecutive_failures}/{max_consecutive_failures})")
                
                if consecutive_failures >= max_consecutive_failures:
                    print(f"⚠️ Frame {frame_count}: Terlalu banyak kegagalan, mencoba reconnect...")
                    consecutive_failures = 0
                    if not reconnect_camera():
                        error_frame = create_error_frame("Reconnection failed")
                        ret, buffer = cv2.imencode('.jpg', error_frame)
                        if ret:
                            frame_bytes = buffer.tobytes()
                            yield (b'--frame\r\n'
                                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                        time.sleep(1)
                        continue
                
                time.sleep(0.1)
                continue
            
            # Successfully read frame
            print(f"✅ Frame {frame_count}: Berhasil membaca frame {frame.shape}")
            consecutive_failures = 0
            reset_reconnect_counter()
            
            # Update frame cache untuk API
            last_frame = frame.copy()
            last_frame_time = time.time()
            
            # Process frame dengan enhanced color detection
            h, w, _ = frame.shape
            
            # Scale frame menggunakan konfigurasi untuk mengurangi zoom
            max_display_width, max_display_height = CameraConfig.get_display_limits()
            
            if CameraConfig.should_scale_frame(w, h):
                # Hitung rasio scaling dari konfigurasi
                scale = CameraConfig.calculate_scale_factor(w, h)
                
                # Resize frame untuk display
                new_w = int(w * scale)
                new_h = int(h * scale)
                display_frame = cv2.resize(frame, (new_w, new_h))
                
                # Sesuaikan koordinat detection box
                box_size = int(CameraConfig.DETECTION_BOX_SIZE * scale)
                top_left_x = new_w // 2 - box_size // 2
                top_left_y = new_h // 2 - box_size // 2
                bottom_right_x = top_left_x + box_size
                bottom_right_y = top_left_y + box_size
                
                # Gunakan ROI dari frame original untuk deteksi akurat
                orig_box_size = CameraConfig.DETECTION_BOX_SIZE
                orig_top_left_x = w // 2 - orig_box_size // 2
                orig_top_left_y = h // 2 - orig_box_size // 2
                orig_bottom_right_x = orig_top_left_x + orig_box_size
                orig_bottom_right_y = orig_top_left_y + orig_box_size
                roi = frame[orig_top_left_y:orig_bottom_right_y, orig_top_left_x:orig_bottom_right_x]
                
                # Draw detection box pada display frame
                cv2.rectangle(display_frame, (top_left_x, top_left_y), (bottom_right_x, bottom_right_y), (0, 255, 0), 2)
                frame = display_frame
            else:
                # Frame sudah dalam ukuran yang sesuai
                box_size = CameraConfig.DETECTION_BOX_SIZE
                top_left_x = w // 2 - box_size // 2
                top_left_y = h // 2 - box_size // 2
                bottom_right_x = top_left_x + box_size
                bottom_right_y = top_left_y + box_size
                
                # Draw detection box
                cv2.rectangle(frame, (top_left_x, top_left_y), (bottom_right_x, bottom_right_y), (0, 255, 0), 2)
                roi = frame[top_left_y:bottom_right_y, top_left_x:bottom_right_x]
            
            # Enhanced preprocessing
            enhanced_roi = enhanced_color_preprocessing(roi)
            
            # Convert to HSV
            hsv = cv2.cvtColor(enhanced_roi, cv2.COLOR_BGR2HSV)
            original_hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
            
            # Adaptive color detection
            pink_mask = adaptive_pink_detection(hsv, roi)
            white_mask = adaptive_white_detection(original_hsv, roi)
            
            # Calculate percentages
            total_pixels = roi.shape[0] * roi.shape[1]
            pink_pixels = cv2.countNonZero(pink_mask)
            white_pixels = cv2.countNonZero(white_mask)
            
            pink_percent = round((pink_pixels / total_pixels) * 100, 2)
            white_percent = round((white_pixels / total_pixels) * 100, 2)
            
            # Color analysis untuk debugging
            color_analysis = analyze_color_distribution(roi)
            
            # Display hasil
            cv2.putText(frame, f'Pink: {pink_percent}%', (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2)
            cv2.putText(frame, f'White: {white_percent}%', (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Debug info
            cv2.putText(frame, f'H:{color_analysis["dominant_hue"]} S:{color_analysis["avg_saturation"]:.0f}', 
                       (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
            
            # Add connection status
            cv2.putText(frame, 'Enhanced Detection', (10, h - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

            # Encode dengan kualitas dari konfigurasi
            encode_params = [cv2.IMWRITE_JPEG_QUALITY, CameraConfig.JPEG_QUALITY]
            ret, buffer = cv2.imencode('.jpg', frame, encode_params)
            if ret:
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            else:
                print("⚠️ Gagal encode frame")
                
        except cv2.error as e:
            print(f"❌ OpenCV Error: {e}")
            consecutive_failures += 1
            
            if consecutive_failures >= max_consecutive_failures:
                print("⚠️ Terlalu banyak OpenCV errors, mencoba reconnect...")
                consecutive_failures = 0
                reconnect_camera()
            
            error_frame = create_error_frame(f"OpenCV Error: {str(e)[:50]}")
            ret, buffer = cv2.imencode('.jpg', error_frame)
            if ret:
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            time.sleep(1)
            
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            consecutive_failures += 1
            
            error_frame = create_error_frame(f"Error: {str(e)[:50]}")
            ret, buffer = cv2.imencode('.jpg', error_frame)
            if ret:
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            time.sleep(1)

def create_error_frame(error_message):
    """Create an error frame to display when camera fails"""
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.putText(frame, 'CAMERA ERROR', (200, 200),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    cv2.putText(frame, error_message, (50, 250),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1)
    cv2.putText(frame, 'Retrying...', (250, 300),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
    return frame

def cleanup_camera():
    """Clean up camera resources"""
    global camera
    try:
        if camera:
            camera.release()
            camera = None
        print("✅ Camera resources cleaned up")
    except Exception as e:
        print(f"⚠️ Error during camera cleanup: {e}")
