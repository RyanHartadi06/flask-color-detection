from flask import Blueprint, Response, jsonify
from app.controllers import item_controller
from app.controllers.color_controller import ColorController

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return item_controller.index()

@main.route('/video_feed')
def video_feed():
    try:
        return Response(ColorController.generate_video_stream(),
                        mimetype='multipart/x-mixed-replace; boundary=frame')
    except Exception as e:
        print(f"❌ Error in video_feed route: {e}")
        return jsonify({'error': 'Video stream not available'}), 500

@main.route('/detect-color')
def detect_color():
    try:
        return ColorController.detect_color()
    except Exception as e:
        print(f"❌ Error in detect_color route: {e}")
        return jsonify({
            'error': 'Color detection service unavailable',
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
