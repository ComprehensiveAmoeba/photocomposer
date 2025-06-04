# Auto Framing Corrector + Debug Tools

This is a lightweight web app built with Streamlit that automatically detects the dominant lines in a photo and straightens the composition. Users can also manually adjust the rotation and experiment with perspective correction. Great for fixing tilted snapshots or composition skew from handheld photography.

---

## 🚀 Features

- ✅ Automatic line detection via Hough Transform (OpenCV)
- ✅ Auto-correction of image alignment
- ✅ Manual angle adjustment with slider
- ✅ Experimental perspective correction (skew)
- ✅ Lightweight JPEG download (85% quality)
- ✅ Visual debug: overlay of detected lines and histogram of angles
- ✅ User data logging (angle delta, country, settings) to external server

---

## 📸 How to Use

1. Upload a JPG or PNG photo.
2. The app auto-corrects rotation based on dominant horizontal/vertical lines.
3. Use the slider to fine-tune the rotation manually.
4. Optionally enable experimental perspective correction.
5. Download the corrected image in lightweight JPEG format.

---

## 📊 Telemetry

The app logs non-personal usage data (angle adjustments, number of lines, download country, perspective toggle) to a server hosted at:

