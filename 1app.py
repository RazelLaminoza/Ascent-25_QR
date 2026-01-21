import streamlit as st
import pandas as pd
import os
import io
import base64
import time
from PIL import Image, ImageDraw, ImageFont
import qrcode
import datetime
import streamlit.components.v1 as components

# ---------------------------
# CONFIG
# ---------------------------
st.set_page_config(page_title="Attendance Scanner", layout="wide")

# ---------------------------
# STYLE + FONT + BACKGROUND
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
            </style>
        """, unsafe_allow_html=True)

def set_background():
    image_path = "bgna.png"
    if os.path.exists(image_path):
        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        st.markdown(f"""
            <style>
            .stApp {{
                background-image: url("data:image/png;base64,{b64}");
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
                background-attachment: fixed;
            }}
            </style>
        """, unsafe_allow_html=True)

add_custom_font()
set_background()

# ---------------------------
# DATA FILES
# ---------------------------
EMPLOYEE_EXCEL = "clean_employees.xlsx"
ATTENDANCE_FILE = "attendance.csv"

# ---------------------------
# LOAD EMPLOYEES
# ---------------------------
def load_employees():
    if not os.path.exists(EMPLOYEE_EXCEL):
        st.error("clean_employees.xlsx not found!")
        return None
    df = pd.read_excel(EMPLOYEE_EXCEL)
    df["emp"] = df["emp"].astype(str)
    return df

# ---------------------------
# ATTENDANCE LOG
# ---------------------------
def load_attendance():
    if os.path.exists(ATTENDANCE_FILE):
        return pd.read_csv(ATTENDANCE_FILE)
    return pd.DataFrame(columns=["name", "emp_id", "status", "timestamp"])

def save_attendance(df):
    df.to_csv(ATTENDANCE_FILE, index=False)

# ---------------------------
# QR Scanner HTML (with camera permission prompt)
# ---------------------------
def qr_scanner_html():
    return """
    <html>
    <head>
      <script src="https://unpkg.com/html5-qrcode" type="text/javascript"></script>
    </head>
    <body>
      <h3 style="text-align:center; color:white;">📷 Allow camera access to scan QR</h3>
      <div id="reader" style="width: 100%;"></div>

      <script>
        function onScanSuccess(decodedText, decodedResult) {
          window.parent.postMessage({ type: 'qr', text: decodedText }, '*');
        }

        function onScanFailure(error) {
          // ignore
        }

        function startScanner() {
          Html5Qrcode.getCameras().then(devices => {
            if (devices && devices.length) {
              const cameraId = devices[devices.length - 1].id; // BACK CAMERA
              let html5QrcodeScanner = new Html5Qrcode("reader");
              html5QrcodeScanner.start(
                cameraId,
                { fps: 10, qrbox: 250 },
                onScanSuccess,
                onScanFailure
              );
            }
          }).catch(err => {
            document.body.innerHTML = "<h3 style='color:red; text-align:center;'>Camera permission denied or not available.</h3>";
          });
        }

        startScanner();
      </script>
    </body>
    </html>
    """

# ---------------------------
# VERIFY QR & LOG
# ---------------------------
def verify_and_log(qr_text, df_emp):
    qr_text = str(qr_text).strip()

    if "|" in qr_text:
        name, emp_id = qr_text.split("|")
        name = name.strip()
        emp_id = emp_id.strip()
    else:
        emp_id = qr_text.strip()
        name = ""

    emp_row = df_emp[df_emp["emp"] == emp_id]

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if emp_row.empty:
        return False, "NOT VERIFIED", emp_id, timestamp, name

    verified_name = emp_row["name"].values[0]

    # prevent double entry
    df_att = load_attendance()
    if emp_id in df_att["emp_id"].astype(str).tolist():
        return True, "ALREADY LOGGED", emp_id, timestamp, verified_name

    return True, "VERIFIED", emp_id, timestamp, verified_name

# ---------------------------
# MAIN APP
# ---------------------------
def main():
    st.title("📌 Attendance Scanner")

    df_emp = load_employees()
    if df_emp is None:
        return

    # --- QR SCANNER ---
    st.subheader("📷 Scan QR (Back Camera)")
    scanner_col, status_col = st.columns([2, 1])

    with scanner_col:
        components.html(qr_scanner_html(), height=450, width=700)

    # --- manual input
    st.subheader("📝 Manual Verification")
    with st.form("manual_form"):
        manual_emp = st.text_input("Enter Employee ID", key="manual_emp")
        manual_submit = st.form_submit_button("Verify")

    if manual_submit:
        st.session_state.qr_text = manual_emp

    # --- listen to QR scan from JS
    if "qr_text" not in st.session_state:
        st.session_state.qr_text = ""

    if st.session_state.get("last_qr", "") != "":
        st.session_state.qr_text = st.session_state.last_qr
        st.session_state.last_qr = ""

    # JS message handler
    message = st.experimental_get_query_params().get("qr", [""])[0]
    if message:
        st.session_state.qr_text = message

    # --- PROCESS QR
    if st.session_state.qr_text:
        ok, status, emp_id, timestamp, name = verify_and_log(st.session_state.qr_text, df_emp)

        df_att = load_attendance()

        if status == "VERIFIED":
            df_att = pd.concat([df_att, pd.DataFrame([{
                "name": name,
                "emp_id": emp_id,
                "status": status,
                "timestamp": timestamp
            }])], ignore_index=True)
            save_attendance(df_att)

        if status == "VERIFIED":
            st.success(f"{status} ✔️ | {name} | {emp_id} | {timestamp}")
        else:
            st.error(f"{status} ❌ | {name} | {emp_id} | {timestamp}")

        st.session_state.qr_text = ""  # reset

    # --- ATTENDANCE TABLE (ONLY VERIFIED)
    st.subheader("🧾 Verified Attendance Log")
    df_att = load_attendance()
    df_verified = df_att[df_att["status"] == "VERIFIED"]
    st.dataframe(df_verified)

if __name__ == "__main__":
    main()
