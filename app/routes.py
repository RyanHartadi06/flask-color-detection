from flask import Blueprint, Response, jsonify, render_template
import time
from app.controllers import item_controller
from app.controllers.color_controller import ColorController
from app.controllers.enhanced_color_controller import EnhancedColorController

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return item_controller.index()

@main.route('/dashboard')
def dashboard():
    """Analytics dashboard page"""
    return render_template('dashboard.html')

@main.route('/debug')
def debug_dashboard():
    """Debug dashboard page for troubleshooting"""
    return render_template('debug_dashboard.html')

@main.route('/analytics')
def analytics():
    """Analytics page with detailed metrics"""
    return render_template('analytics.html')

@main.route('/test-stream')
def test_stream():
    """Test video stream with simple frame generation"""
    def generate_test_frames():
        import cv2
        import numpy as np
        
        for i in range(10):  # Generate 10 test frames
            # Create a simple test frame
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            frame[:] = (50, 50, 50)  # Dark gray background
            
            # Add text
            cv2.putText(frame, f'Test Frame {i+1}', (50, 240), 
                       cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
            
            # Encode to JPEG
            ret, buffer = cv2.imencode('.jpg', frame)
            if ret:
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            time.sleep(0.5)  # 0.5 second delay
    
    return Response(generate_test_frames(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@main.route('/debug-rtsp')
def debug_rtsp():
    """Debug RTSP connection and frame reading"""
    try:
        from app.services.enhanced_color_service import camera, rtsp_url
        
        result = {
            'rtsp_url': rtsp_url,
            'camera_object': str(camera),
            'is_opened': camera.isOpened() if camera else False,
        }
        
        if camera and camera.isOpened():
            # Try to read one frame
            ret, frame = camera.read()
            result.update({
                'frame_read_success': ret,
                'frame_shape': frame.shape if ret and frame is not None else None,
                'frame_type': str(type(frame)) if ret and frame is not None else None
            })
        
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'error': str(e),
            'error_type': type(e).__name__
        })

@main.route('/video_feed')
def video_feed():
    try:
        # Use enhanced video stream untuk deteksi yang lebih baik
        return Response(EnhancedColorController.generate_video_stream(),
                        mimetype='multipart/x-mixed-replace; boundary=frame')
    except Exception as e:
        print(f"❌ Error in enhanced video_feed route: {e}")
        return jsonify({'error': 'Enhanced video stream not available'}), 500

@main.route('/video_feed_original')
def video_feed_original():
    """Original video feed untuk comparison"""
    try:
        return Response(ColorController.generate_video_stream(),
                        mimetype='multipart/x-mixed-replace; boundary=frame')
    except Exception as e:
        print(f"❌ Error in original video_feed route: {e}")
        return jsonify({'error': 'Original video stream not available'}), 500

@main.route('/detect-color')
def detect_color():
    try:
        # Use enhanced color detection
        return EnhancedColorController.detect_color()
    except Exception as e:
        print(f"❌ Error in enhanced detect_color route: {e}")
        return jsonify({
            'error': 'Enhanced color detection service unavailable',
            'pink': 0, 
            'white': 0,
            'status': 'service_error',
            'debug_info': {}
        }), 500

@main.route('/test')
def test():
    """Simple test endpoint to verify Flask is working"""
    return jsonify({
        'status': 'ok',
        'message': 'Flask app is running',
        'timestamp': time.time()
    })

@main.route('/test-video')
def test_video():
    """Test video feed endpoint"""
    try:
        from app.services.enhanced_color_service import camera
        if camera and camera.isOpened():
            return jsonify({
                'status': 'ok',
                'camera': 'connected',
                'message': 'Camera is accessible'
            })
        else:
            return jsonify({
                'status': 'error',
                'camera': 'disconnected',
                'message': 'Camera not accessible'
            })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'message': 'Error checking camera'
        })

@main.route('/detect-color-original')
def detect_color_original():
    """Original color detection untuk comparison"""
    try:
        return ColorController.detect_color()
    except Exception as e:
        print(f"❌ Error in original detect_color route: {e}")
        return jsonify({
            'error': 'Original color detection service unavailable',
            'pink': 0, 
            'white': 0,
            'status': 'service_error'
        }), 500

@main.route('/camera-status')
def camera_status():
    """Check camera connection status"""
    from app.services.color_service import camera
    try:
        if camera and camera.isOpened():
            return jsonify({'status': 'connected', 'message': 'Camera is connected'})
        else:
            return jsonify({'status': 'disconnected', 'message': 'Camera is not connected'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error checking camera: {str(e)}'})
