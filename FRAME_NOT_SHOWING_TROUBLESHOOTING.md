# 🔧 Troubleshooting: Frame Tidak Muncul

## 🎯 Masalah

**Problem**: Frame RTSP tidak muncul di browser, hanya loading screen yang tampil

## ✅ Status Sistem Saat Ini

- ✅ Flask app running di port 5000
- ✅ RTSP connection berhasil (Resolution: 640x360)
- ✅ Enhanced color service loaded
- ✅ Config loaded successfully
- ❌ Video feed tidak tampil di browser

## 🔍 Langkah Troubleshooting

### 1. **Check Browser Console**

Buka Developer Tools (F12) di browser dan periksa:

```javascript
// Console akan menampilkan:
// "Video feed element found, source: /video_feed"
// "Video feed error event: ..." (jika ada error)
```

### 2. **Test Direct Video Feed URL**

Buka langsung di browser:

```
http://127.0.0.1:5000/video_feed
```

**Expected**: Stream MJPEG atau error message

### 3. **Test Alternative Feeds**

```
http://127.0.0.1:5000/video_feed_original  # Original feed
http://127.0.0.1:5000/detect-color         # JSON response
```

### 4. **Check Network Tab**

Di Developer Tools → Network:

- Lihat apakah request ke `/video_feed` berhasil
- Status code yang diharapkan: `200 OK`
- Content-Type: `multipart/x-mixed-replace; boundary=frame`

## 🛠️ Solusi yang Sudah Diimplementasikan

### **Enhanced Error Handling**

```javascript
function handleVideoError(img) {
  console.error("Video feed error occurred:", img.src);
  // Menampilkan error screen dengan tombol retry
}
```

### **Fallback Feed Switch**

```javascript
function switchToOriginalFeed() {
  // Switch ke /video_feed_original jika enhanced gagal
}
```

### **Config Fallback**

```python
# Jika config import gagal, gunakan default values
class CameraConfig:
    RTSP_URL = 'rtsp://admin:Petro%402025@...'
    TARGET_WIDTH = 1280
    TARGET_HEIGHT = 720
```

## 🔧 Manual Fixes

### **Fix 1: Force Reload Video Feed**

```javascript
// Di browser console:
const video = document.getElementById("videoFeed");
video.src = "/video_feed?t=" + Date.now();
```

### **Fix 2: Switch to Original Feed**

```javascript
// Di browser console:
switchToOriginalFeed();
```

### **Fix 3: Check Video Element**

```javascript
// Di browser console:
const video = document.getElementById("videoFeed");
console.log("Video src:", video.src);
console.log("Video display:", getComputedStyle(video).display);
```

## 📊 Expected Behavior

### **Normal Flow:**

1. ✅ Page loads → Loading spinner appears
2. ✅ Video feed loads → Loading spinner disappears
3. ✅ Stream displays → Detection box visible
4. ✅ Real-time updates → Pink/white percentages update

### **Error Flow:**

1. ❌ Video feed fails → Error screen appears
2. 🔄 Click "Retry Connection" → Reload attempt
3. 🔄 Click "Original Feed" → Switch to backup stream

## 🚨 Common Issues & Solutions

### **Issue 1: Black Screen**

**Cause**: RTSP stream not accessible
**Solution**:

```python
# Check RTSP URL in enhanced_color_service.py
rtsp_url = 'rtsp://admin:Petro%402025@10.14.66.163:554/...'
```

### **Issue 2: Loading Forever**

**Cause**: Video feed endpoint not responding
**Solution**:

```python
# Check routes.py for /video_feed endpoint
# Ensure EnhancedColorController.generate_video_stream() works
```

### **Issue 3: Console Errors**

**Cause**: CORS, network, or JavaScript errors
**Solution**: Check browser console for specific error messages

## 🎯 Quick Test Commands

### **Test Flask App**

```bash
curl http://127.0.0.1:5000/
```

### **Test Video Feed**

```bash
curl http://127.0.0.1:5000/video_feed --max-time 5
```

### **Test Detection API**

```bash
curl http://127.0.0.1:5000/detect-color
```

## 📝 Debug Info

### **Browser Console Commands:**

```javascript
// Check video element
document.getElementById("videoFeed");

// Manual reload
retryVideoConnection();

// Switch feed
switchToOriginalFeed();

// Check connection status
fetch("/detect-color")
  .then((r) => r.json())
  .then(console.log);
```

---

**Next Steps**:

1. Open browser Developer Tools (F12)
2. Go to http://127.0.0.1:5000
3. Check Console and Network tabs for errors
4. Try manual fixes above
5. Report specific error messages found
