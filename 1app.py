import streamlit as st
import pandas as pd
import os
import base64
import time
import datetime
from PIL import Image, ImageDraw, ImageFont
from streamlit.components.v1 import components

# ---------------------------
# Constants
# ---------------------------
EMPLOYEE_EXCEL = "clean_employees.xlsx"
ATTENDANCE_FILE = "attendance.csv"

# ---------------------------
# Styles (Same as your main app)
# ---------------------------
st.markdown("""
<style>
/* FULL KIOSK LOCKDOWN */
[data-testid="stToolbar"] { display: none !important; }
[data-testid="stDeployButton"] { display: none !important; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header { visibility: hidden; }
html, body { overflow: hidden !important; height: 150%; }
.block-container { padding: 0 !important; }
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Custom Font
# ---------------------------
def add_custom_font():
    font_path = "PPNeueMachina-PlainUltrabold.ttf"
    if os.path.exists(font_path):
        with open(font_path, "rb") as f:
            font_b64 = base64.b64encode(f.read()).decode()
        st.markdown(f"""
            <style>
                @font-face {{
                    font-family: "PPNeueMachina";
                    src: url("data:font/ttf;base64,{font_b64}") format("truetype");
                }}
                * {{
                    font-family: "PPNeueMachina" !important;
                }}
                button, input, textarea, select {{
                    font-family: "PPNeueMachina" !important;
                }}
            </style>
        """, unsafe_allow_html=True)

add_custom_font()

# ---------------------------
# Background
# ---------------------------
def set_background():
    image_path = "bgna.png"
    if os.path.exists(image_path):
        with open(image_path, "rb") as f:
            data = f.read()
        b64 = base64.b64encode(data).decode()

        st.markdown(
            f"""
            <style>
            .stApp {{
                background-image: url("data:image/png;base64,{b64}");
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
                background-attachment: fixed;
            }}
            </style>
            """,
            unsafe_allow_html=True,
        )

set_background()

# ---------------------------
# Data
# ---------------------------
def load_attendance():
    if os.path.exists(ATTENDANCE_FILE):
        return pd.read_csv(ATTENDANCE_FILE)
    else:
        return pd.DataFrame(columns=["name", "emp_id", "time"])

def save_attendance(df):
    df.to_csv(ATTENDANCE_FILE, index=False)

# ---------------------------
# QR Scanner Component
# ---------------------------
def qr_scanner():
    components.html(
        """
        <html>
        <head>
          <script src="https://unpkg.com/html5-qrcode" type="text/javascript"></script>
        </head>
        <body>
        <div style="width:100%; text-align:center;">
            <div id="reader" style="width: 400px; margin: 0 auto;"></div>
            <p id="result"></p>
        </div>
        <script>
            function onScanSuccess(decodedText, decodedResult) {
                document.getElementById('result').innerText = decodedText;
                window.parent.postMessage({ type: 'qr', text: decodedText }, '*');
            }

            function onScanFailure(error) {
                // ignore
            }

            let html5QrcodeScanner = new Html5QrcodeScanner(
                "reader", { fps: 10, qrbox: 250 });
            html5QrcodeScanner.render(onScanSuccess, onScanFailure);
        </script>
        </body>
        </html>
        """,
        height=450,
        width=600,
    )

# ---------------------------
# Main Page
# ---------------------------
def main():
    st.markdown("<h1 style='text-align:center; color:#FFD700;'>QR Attendance Scanner</h1>", unsafe_allow_html=True)

    st.markdown("<p style='text-align:center; color:white;'>Scan QR to mark attendance</p>", unsafe_allow_html=True)

    # QR Scanner
    qr_scanner()

    # Receive QR result
    qr_text = st.experimental_get_query_params().get("qr", [""])[0]
    scanned = st.text_input("Scanned QR (Auto):", key="scanned_qr")

    # Verify and record attendance
    if scanned:
        emp_id = scanned.split("|")[-1].strip()

        if not os.path.exists(EMPLOYEE_EXCEL):
            st.error("Employee Excel file not found.")
            return

        df_employees = pd.read_excel(EMPLOYEE_EXCEL)

        if emp_id in df_employees["emp"].astype(str).tolist():
            name = df_employees[df_employees["emp"].astype(str) == emp_id]["name"].values[0]
            df_att = load_attendance()

            # Avoid duplicate attendance
            if emp_id in df_att["emp_id"].astype(str).tolist():
                st.warning("Attendance already recorded.")
            else:
                df_att = df_att.append({
                    "name": name,
                    "emp_id": emp_id,
                    "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }, ignore_index=True)
                save_attendance(df_att)
                st.success(f"Attendance recorded for {name} ({emp_id})")
        else:
            st.error("Employee NOT VERIFIED ❌")

    st.markdown("---")
    st.markdown("<h2 style='color:#FFD700;'>Attendance Table</h2>", unsafe_allow_html=True)
    st.dataframe(load_attendance())

if __name__ == "__main__":
    main()

