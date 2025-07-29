import cv2
import numpy as np
import time
import threading

# Ganti dengan URL RTSP CCTV
rtsp_url = 'rtsp://admin:Petro%402025@10.14.66.163:554/Streaming/Channels/102?transportmode=unicast'
camera = None
camera_lock = threading.Lock()
reconnect_attempts = 0
max_reconnect_attempts = 5
base_reconnect_delay = 1

def init_camera():
    global camera
    try:
        if camera:
            camera.release()
        camera = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
        # Set buffer size to reduce latency
        camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        # Set timeout
        camera.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)
        camera.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000)
        
        if not camera.isOpened():
            print("❌ Tidak bisa membuka RTSP stream")
            return False
        
        # Test read to make sure connection works
        ret, test_frame = camera.read()
        if not ret or test_frame is None:
            print("❌ Tidak bisa membaca frame test")
            camera.release()
            camera = None
            return False
            
        print("✅ Berhasil koneksi ke RTSP stream")
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
        delay = min(base_reconnect_delay * (2 ** (reconnect_attempts - 1)), 30)  # Exponential backoff, max 30 seconds
        
        print(f"🔁 Reconnect attempt {reconnect_attempts}/{max_reconnect_attempts} after {delay}s delay...")
        time.sleep(delay)
        
        try:
            if camera:
                camera.release()
                camera = None
            
            return init_camera()
            
        except Exception as e:
            print(f"❌ Gagal reconnect: {e}")
            return False

def reset_reconnect_counter():
    global reconnect_attempts
    reconnect_attempts = 0

# Initialize camera
if not init_camera():
    print("⚠️ Gagal initial connection, akan mencoba reconnect saat streaming dimulai")

def generate_video_stream():
    global camera
    
    consecutive_failures = 0
    max_consecutive_failures = 10
    
    while True:
        try:
            # Check if camera is available
            if camera is None or not camera.isOpened():
                print("⚠️ Camera tidak tersedia, mencoba reconnect...")
                if not reconnect_camera():
                    # Return error frame
                    error_frame = create_error_frame("Camera disconnected")
                    ret, buffer = cv2.imencode('.jpg', error_frame)
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                    time.sleep(1)
                    continue
            
            with camera_lock:
                ret, frame = camera.read()
            
            if not ret or frame is None:
                consecutive_failures += 1
                print(f"⚠️ Gagal membaca frame ({consecutive_failures}/{max_consecutive_failures})")
                
                if consecutive_failures >= max_consecutive_failures:
                    print("⚠️ Terlalu banyak kegagalan berturut-turut, mencoba reconnect...")
                    consecutive_failures = 0
                    if not reconnect_camera():
                        # Return error frame
                        error_frame = create_error_frame("Reconnection failed")
                        ret, buffer = cv2.imencode('.jpg', error_frame)
                        frame_bytes = buffer.tobytes()
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                        time.sleep(1)
                        continue
                
                time.sleep(0.1)  # Short delay before retry
                continue
            
            # Reset failure counter on successful read
            consecutive_failures = 0
            reset_reconnect_counter()  # Reset reconnect attempts on successful frame
            
            # Process frame
            h, w, _ = frame.shape
            box_size = 200
            top_left_x = w // 2 - box_size // 2
            top_left_y = h // 2 - box_size // 2
            bottom_right_x = top_left_x + box_size
            bottom_right_y = top_left_y + box_size

            cv2.rectangle(frame, (top_left_x, top_left_y), (bottom_right_x, bottom_right_y), (0, 255, 0), 2)
            roi = frame[top_left_y:bottom_right_y, top_left_x:bottom_right_x]
            
            # Color detection
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

            cv2.putText(frame, f'Pink: {pink_percent}%', (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2)
            cv2.putText(frame, f'White: {white_percent}%', (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Add connection status
            cv2.putText(frame, 'Connected', (10, h - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

            ret, buffer = cv2.imencode('.jpg', frame)
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
            
            # Return error frame
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
            
            # Return error frame
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
