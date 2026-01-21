import streamlit as st
import pandas as pd
import os
import base64
import datetime
import streamlit.components.v1 as components

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
        return pd.DataFrame(columns=["name", "emp_id", "date", "time"])

def save_attendance(df):
    df.to_csv(ATTENDANCE_FILE, index=False)

# ---------------------------
# Read Employee File
# ---------------------------
def read_employee_file():
    if os.path.exists("clean_employees.xlsx"):
        return pd.read_excel("clean_employees.xlsx")
    else:
        st.error("Employee Excel file not found.")
        return None

# ---------------------------
# QR Scanner Component (BACK CAMERA)
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
        </div>

        <script>
            function onScanSuccess(decodedText, decodedResult) {
                // send scanned QR to Streamlit
                window.parent.postMessage({ type: 'qr_scanned', text: decodedText }, '*');
            }

            function onScanFailure(error) {
                // ignore
            }

            let html5QrcodeScanner = new Html5QrcodeScanner(
                "reader",
                {
                    fps: 10,
                    qrbox: 250,
                    videoConstraints: {
                        facingMode: { exact: "environment" }
                    }
                }
            );

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

    # Initialize session state
    if "scanned_qr" not in st.session_state:
        st.session_state.scanned_qr = ""

    qr_scanner()

    # ---- JS Message Listener ----
    st.write(
        """
        <script>
        const streamlitReceive = (event) => {
            if (event.data && event.data.type === 'qr_scanned') {
                window.parent.postMessage({ type: 'set_qr', text: event.data.text }, '*');
            }
        };
        window.addEventListener('message', streamlitReceive);
        </script>
        """,
        unsafe_allow_html=True
    )

    # ---- Receive QR from JS ----
    qr = st.experimental_get_query_params().get("qr", [""])[0]
    if qr:
        st.session_state.scanned_qr = qr

    # ---- Hidden QR input ----
    scanned = st.text_input("Scanned QR:", value=st.session_state.scanned_qr, key="scanned_qr_input")

    # Process QR automatically
    if scanned and scanned != "":
        process_qr(scanned)

    st.markdown("---")
    st.markdown("<h2 style='color:#FFD700;'>Attendance Table</h2>", unsafe_allow_html=True)
    st.dataframe(load_attendance())


def process_qr(scanned):
    parts = scanned.split("|")
    if len(parts) != 2:
        st.error("Invalid QR format. Use: Name | EmpID")
        return

    name_qr = parts[0].strip()
    emp_id = parts[1].strip()

    df_employees = read_employee_file()
    if df_employees is None:
        return

    if emp_id in df_employees["emp"].astype(str).tolist():
        name = df_employees[df_employees["emp"].astype(str) == emp_id]["name"].values[0]
        st.success(f"VERIFIED: {name} | {emp_id}")

        df_att = load_attendance()
        today = (datetime.datetime.utcnow() + datetime.timedelta(hours=8)).strftime("%Y-%m-%d")
        now_pht = (datetime.datetime.utcnow() + datetime.timedelta(hours=8)).strftime("%H:%M:%S")

        if ((df_att["emp_id"].astype(str) == emp_id) & (df_att["date"] == today)).any():
            st.warning("Attendance already recorded today.")
        else:
            new_row = pd.DataFrame([{
                "name": name,
                "emp_id": emp_id,
                "date": today,
                "time": now_pht
            }])
            df_att = pd.concat([df_att, new_row], ignore_index=True)
            save_attendance(df_att)
            st.success(f"Attendance recorded for {name} ({emp_id})")
    else:
        st.error("Employee NOT VERIFIED ❌")


if __name__ == "__main__":
    main()
