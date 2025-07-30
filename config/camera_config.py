# RTSP Camera Configuration
# File ini berisi pengaturan untuk mengatasi masalah zoom berlebihan dan optimasi RTSP

class CameraConfig:
    # RTSP Settings
    RTSP_URL = 'rtsp://admin:Petro%402025@10.14.66.163:554/Streaming/Channels/102?transportmode=unicast'
    
    # Resolution Settings - untuk mengurangi zoom
    TARGET_WIDTH = 1280        # Resolusi lebar yang diinginkan (bisa disesuaikan: 1920, 1280, 1024, 800)
    TARGET_HEIGHT = 720        # Resolusi tinggi yang diinginkan (bisa disesuaikan: 1080, 720, 576, 600)
    
    # Display Settings - untuk mengontrol ukuran tampilan
    MAX_DISPLAY_WIDTH = 1024   # Maksimal lebar tampilan di web browser
    MAX_DISPLAY_HEIGHT = 768   # Maksimal tinggi tampilan di web browser
    
    # Frame Settings
    TARGET_FPS = 15           # FPS yang diinginkan untuk stabilitas
    BUFFER_SIZE = 1           # Buffer size untuk mengurangi latency
    
    # Detection Box Settings
    DETECTION_BOX_SIZE = 200  # Ukuran kotak deteksi di tengah frame
    
    # Connection Settings
    OPEN_TIMEOUT = 5000       # Timeout untuk membuka koneksi (ms)
    READ_TIMEOUT = 5000       # Timeout untuk membaca frame (ms)
    
    # Quality Settings - untuk mengoptimalkan streaming
    JPEG_QUALITY = 85         # Kualitas JPEG encoding (1-100)
    
    @classmethod
    def get_optimal_resolution(cls):
        """
        Mengembalikan resolusi optimal berdasarkan pengaturan
        """
        return (cls.TARGET_WIDTH, cls.TARGET_HEIGHT)
    
    @classmethod
    def get_display_limits(cls):
        """
        Mengembalikan batas maksimal untuk tampilan
        """
        return (cls.MAX_DISPLAY_WIDTH, cls.MAX_DISPLAY_HEIGHT)
    
    @classmethod
    def should_scale_frame(cls, frame_width, frame_height):
        """
        Menentukan apakah frame perlu di-scale untuk mengurangi zoom
        """
        return (frame_width > cls.MAX_DISPLAY_WIDTH or 
                frame_height > cls.MAX_DISPLAY_HEIGHT)
    
    @classmethod
    def calculate_scale_factor(cls, frame_width, frame_height):
        """
        Menghitung faktor scale yang diperlukan
        """
        scale_w = cls.MAX_DISPLAY_WIDTH / frame_width
        scale_h = cls.MAX_DISPLAY_HEIGHT / frame_height
        return min(scale_w, scale_h)

# Pengaturan untuk berbagai resolusi CCTV yang umum
RESOLUTION_PRESETS = {
    'HD_READY': (1280, 720),      # Recommended untuk mengurangi zoom
    'FULL_HD': (1920, 1080),      # Mungkin terlalu zoom
    'ULTRA_WIDE': (1920, 1200),   # Untuk monitor ultra-wide
    'STANDARD': (1024, 768),      # Untuk koneksi yang lambat
    'MOBILE': (800, 600),         # Untuk mobile/tablet
}

# Tips Penggunaan:
# 1. Jika RTSP terlihat sangat zoom, gunakan TARGET_WIDTH = 1024, TARGET_HEIGHT = 768
# 2. Jika kualitas kurang bagus, naikkan JPEG_QUALITY ke 90-95
# 3. Jika streaming lambat, turunkan TARGET_FPS ke 10-12
# 4. Jika ingin tampilan lebih kecil, turunkan MAX_DISPLAY_WIDTH/HEIGHT
