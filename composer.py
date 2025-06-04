import streamlit as st
import cv2
import numpy as np
from PIL import Image
from io import BytesIO
import matplotlib.pyplot as plt
import requests
import datetime
import json

st.set_page_config(page_title="Auto Framing Corrector", layout="centered")

st.title("📐 Auto Framing Corrector + Debug Tools")
st.markdown(
    "Upload an image and this tool will detect dominant lines to automatically straighten it. "
    "You can also manually adjust the rotation if needed, and even apply experimental perspective correction!"
)

def detect_and_correct_image(image_bytes, manual_angle=None, perspective=False):
    file_bytes = np.asarray(bytearray(image_bytes), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    original_shape = img.shape[:2]

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150, apertureSize=3)

    lines = cv2.HoughLines(edges, 1, np.pi / 180, 250)
    angles = []
    line_img = img.copy()

    if lines is not None:
        for rho, theta in lines[:, 0]:
            angle_deg = (theta - np.pi / 2) * (180 / np.pi)
            if -20 <= angle_deg <= 20 or 70 <= abs(angle_deg) <= 110:
                angles.append(angle_deg)
                a = np.cos(theta)
                b = np.sin(theta)
                x0 = a * rho
                y0 = b * rho
                x1 = int(x0 + 1000 * (-b))
                y1 = int(y0 + 1000 * (a))
                x2 = int(x0 - 1000 * (-b))
                y2 = int(y0 - 1000 * (a))
                cv2.line(line_img, (x1, y1), (x2, y2), (0, 255, 0), 2)

    auto_angle = np.median(angles) if angles else 0
    applied_angle = manual_angle if manual_angle is not None else auto_angle

    (h, w) = img.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, applied_angle, 1.0)
    rotated = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

    if perspective:
        src_pts = np.float32([
            [w * 0.05, h * 0.05],
            [w * 0.95, h * 0.05],
            [w * 0.05, h * 0.95],
            [w * 0.95, h * 0.95],
        ])
        dst_pts = np.float32([
            [0, 0],
            [w, 0],
            [0, h],
            [w, h],
        ])
        perspective_matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)
        rotated = cv2.warpPerspective(rotated, perspective_matrix, (w, h), borderMode=cv2.BORDER_REPLICATE)

    corrected = cv2.resize(rotated, (original_shape[1], original_shape[0]))
    original_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    corrected_rgb = cv2.cvtColor(corrected, cv2.COLOR_BGR2RGB)
    lines_rgb = cv2.cvtColor(line_img, cv2.COLOR_BGR2RGB)

    return {
        "original": Image.fromarray(original_rgb),
        "corrected": Image.fromarray(corrected_rgb),
        "lines_debug": Image.fromarray(lines_rgb),
        "auto_angle": auto_angle,
        "angles_list": angles
    }

def convert_image_to_bytes(img, format="JPEG", quality=85):
    buf = BytesIO()
    img.save(buf, format=format, quality=quality)
    return buf.getvalue()

def log_download_to_server(data):
    try:
        response = requests.post(
            "https://campsnaptools.com/receive.php",
            data=json.dumps(data),
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        if response.status_code != 200:
            st.warning(f"⚠️ Error al enviar log: {response.status_code}")
    except Exception as e:
        st.warning(f"⚠️ No se pudo registrar la descarga: {e}")

# Upload
uploaded_file = st.file_uploader("Upload your photo", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    result = detect_and_correct_image(uploaded_file.read())

    # Corrección manual + skew (experimental)
    angle = st.slider("🌀 Manual rotation (degrees)", -45.0, 45.0, float(result["auto_angle"]), 0.1)
    perspective_mode = st.checkbox("🧪 Enable experimental perspective correction")

    # Aplicar transformación completa
    uploaded_file.seek(0)
    final_result = detect_and_correct_image(uploaded_file.read(), manual_angle=angle, perspective=perspective_mode)

    st.subheader("Before vs Corrected")
    col1, col2 = st.columns(2)
    with col1:
        st.image(final_result["original"], caption="Original", use_column_width=True)
    with col2:
        st.image(final_result["corrected"], caption=f"Corrected (angle: {angle:.2f}°)", use_column_width=True)

    # Descarga JPEG
    download = st.download_button(
        label="📥 Download Corrected Image (JPEG 85%)",
        data=convert_image_to_bytes(final_result["corrected"]),
        file_name="corrected_image.jpg",
        mime="image/jpeg"
    )

    # Enviar log tras descarga
    if download:
        try:
            country_info = requests.get("https://ipapi.co/json", timeout=3).json()
            client_country = country_info.get("country_name")
        except:
            client_country = "Unknown"

        log_data = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "filename": uploaded_file.name,
            "auto_angle": result["auto_angle"],
            "manual_angle": angle,
            "correction_delta": angle - result["auto_angle"],
            "num_lines": len(result["angles_list"]),
            "client_country": client_country,
            "perspective_mode": perspective_mode,
            "key": "superpat"
        }

        log_download_to_server(log_data)

    st.subheader("🧠 Detected Lines (Debug View)")
    st.image(result["lines_debug"], caption="Lines detected via Hough Transform", use_column_width=True)

    if result["angles_list"]:
        st.subheader("📊 Angle Histogram")
        fig, ax = plt.subplots()
        ax.hist(result["angles_list"], bins=30, color="#4f8bf9", edgecolor="black")
        ax.set_xlabel("Angle (degrees)")
        ax.set_ylabel("Frequency")
        ax.set_title("Distribution of Detected Line Angles")
        st.pyplot(fig)
    else:
        st.info("No significant lines detected. Try another image.")
