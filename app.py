import atexit
import signal
import sys
from app import create_app
from app.services.color_service import cleanup_camera

app = create_app()

def cleanup_handler():
    """Cleanup resources when app shuts down"""
    print("🧹 Cleaning up resources...")
    cleanup_camera()

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n⚠️ Received interrupt signal")
    cleanup_handler()
    sys.exit(0)

# Register cleanup handlers
atexit.register(cleanup_handler)
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if __name__ == '__main__':
    try:
        print("🚀 Starting Flask Color Detection App...")
        app.run(debug=True, use_reloader=False)  # Disable reloader to avoid double cleanup
    except KeyboardInterrupt:
        print("\n⚠️ App interrupted by user")
        cleanup_handler()
    except Exception as e:
        print(f"❌ App crashed: {e}")
        cleanup_handler()
        raise