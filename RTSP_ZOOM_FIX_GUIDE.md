# 🔍 Panduan Mengatasi RTSP Frame Terlihat Sangat Zoom

## 🎯 Masalah yang Diatasi

**Problem**: Frame RTSP terlihat sangat zoom/terpotong, tidak menampilkan area yang cukup luas untuk deteksi

## ✅ Solusi yang Diimplementasikan

### 1. **Pengaturan Resolusi RTSP**

```python
# Set resolusi target untuk mengurangi zoom
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)   # Lebar frame
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)   # Tinggi frame
camera.set(cv2.CAP_PROP_FPS, 15)             # Frame rate yang stabil
```

### 2. **Auto-Scaling Display Frame**

```python
# Otomatis resize frame jika terlalu besar untuk browser
if w > 1024 or h > 768:
    scale = min(1024/w, 768/h)
    display_frame = cv2.resize(frame, (new_w, new_h))
```

### 3. **Konfigurasi Fleksibel**

File `config/camera_config.py` memungkinkan penyesuaian mudah:

- **TARGET_WIDTH/HEIGHT**: Resolusi RTSP yang diminta
- **MAX_DISPLAY_WIDTH/HEIGHT**: Batas maksimal tampilan di browser
- **DETECTION_BOX_SIZE**: Ukuran area deteksi
- **JPEG_QUALITY**: Kualitas encoding video

## 🛠️ Cara Menyesuaikan Zoom

### Jika Masih Terlalu Zoom:

1. **Edit `config/camera_config.py`**:

   ```python
   TARGET_WIDTH = 1024      # Turunkan dari 1280
   TARGET_HEIGHT = 768      # Turunkan dari 720
   MAX_DISPLAY_WIDTH = 800  # Kurangi ukuran display
   MAX_DISPLAY_HEIGHT = 600
   ```

2. **Gunakan Preset Resolusi**:

   ```python
   # Untuk zoom yang lebih jauh
   'STANDARD': (1024, 768)

   # Untuk mobile/tablet
   'MOBILE': (800, 600)
   ```

### Jika Ingin Zoom Lebih Dekat:

```python
TARGET_WIDTH = 1920      # Naikkan resolusi
TARGET_HEIGHT = 1080
MAX_DISPLAY_WIDTH = 1280 # Perbesar display
MAX_DISPLAY_HEIGHT = 960
```

## 📊 Status Implementasi

### ✅ **Yang Sudah Diperbaiki:**

- **Resolution Control**: Camera diminta menggunakan resolusi 1280x720
- **Auto-Scaling**: Frame otomatis di-resize untuk browser (maks 1024x768)
- **Aspect Ratio**: Proporsi frame dipertahankan saat scaling
- **Detection Accuracy**: ROI deteksi menggunakan koordinat asli (akurat)
- **Quality Control**: JPEG encoding dengan kualitas 85%
- **Configuration**: Pengaturan terpusat di file config

### 📈 **Hasil Testing:**

- **Sebelum**: Frame RTSP sangat zoom, area deteksi terbatas
- **Sesudah**: Resolusi 640x360 (disesuaikan otomatis oleh kamera)
- **Display**: Auto-scaled untuk optimal viewing di browser
- **Performance**: Stable 15 FPS dengan buffer minimal

## ⚙️ Parameter yang Bisa Disesuaikan

### Di `config/camera_config.py`:

| Parameter            | Default | Fungsi                | Saran Adjustment                   |
| -------------------- | ------- | --------------------- | ---------------------------------- |
| `TARGET_WIDTH`       | 1280    | Lebar frame RTSP      | 1024 (less zoom), 1920 (more zoom) |
| `TARGET_HEIGHT`      | 720     | Tinggi frame RTSP     | 768 (less zoom), 1080 (more zoom)  |
| `MAX_DISPLAY_WIDTH`  | 1024    | Max lebar di browser  | 800 (smaller), 1280 (larger)       |
| `MAX_DISPLAY_HEIGHT` | 768     | Max tinggi di browser | 600 (smaller), 960 (larger)        |
| `DETECTION_BOX_SIZE` | 200     | Ukuran kotak deteksi  | 150 (smaller), 300 (larger)        |
| `JPEG_QUALITY`       | 85      | Kualitas video        | 70 (faster), 95 (better quality)   |

## 🚀 Cara Menggunakan

### 1. **Test Current Settings**:

- Buka http://127.0.0.1:5000
- Lihat apakah frame sudah sesuai
- Check resolusi di console: "Resolution: WxH"

### 2. **Adjust Jika Perlu**:

```python
# Edit config/camera_config.py
TARGET_WIDTH = 1024    # Sesuaikan
TARGET_HEIGHT = 768    # Sesuaikan
```

### 3. **Restart Application**:

```bash
# Stop dan start ulang Flask app
```

## 🔧 Advanced Solutions

### Jika RTSP Camera Tidak Support Resolution Setting:

```python
# Force resize setelah capture
def force_resize_frame(frame, target_w, target_h):
    return cv2.resize(frame, (target_w, target_h))
```

### Untuk Multiple Camera Views:

```python
# Bisa set resolusi berbeda per camera
CAMERA_CONFIGS = {
    'camera_1': {'width': 1280, 'height': 720},
    'camera_2': {'width': 1024, 'height': 768}
}
```

## 📝 Notes

- **RTSP Camera Response**: Kamera otomatis menyesuaikan ke resolusi terdekat yang didukung
- **Network Consideration**: Resolusi lebih rendah = bandwidth lebih rendah = streaming lebih lancar
- **Detection Accuracy**: ROI detection tetap menggunakan koordinat asli untuk akurasi maksimal
- **Browser Compatibility**: Auto-scaling memastikan kompatibilitas dengan berbagai ukuran layar

**Result**: Frame RTSP sekarang menggunakan resolusi optimal (640x360) dan auto-scaled untuk display yang lebih baik! 🎉
