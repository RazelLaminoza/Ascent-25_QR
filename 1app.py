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
# Styles
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
    if os.path.exists(EMPLOYEE_EXCEL):
        return pd.read_excel(EMPLOYEE_EXCEL)
    else:
        st.error("Employee Excel file not found.")
        return None

# ---------------------------
# QR Scanner Component (BACK CAMERA)
# ---------------------------
def qr_scanner():
    qr_html = """
    <html>
    <head>
      <script src="https://unpkg.com/html5-qrcode" type="text/javascript"></script>
    </head>
    <body>
    <div style="width:100%; text-align:center;">
        <div id="reader" style="width: 100%; margin: 0 auto;"></div>
    </div>
    <script>
        function onScanSuccess(decodedText, decodedResult) {
            window.parent.postMessage({ type: 'qr', text: decodedText }, '*');
        }

        function onScanFailure(error) {
            // ignore
        }

        Html5Qrcode.getCameras().then(devices => {
            if (devices && devices.length) {
                let backCamera = devices.find(d => d.label.toLowerCase().includes("back")) || devices[0];

                const html5Qrcode = new Html5Qrcode("reader");
                html5Qrcode.start(
                    { deviceId: { exact: backCamera.id } },
                    { fps: 10, qrbox: 250 },
                    onScanSuccess,
                    onScanFailure
                );
            }
        }).catch(err => {
            document.getElementById('reader').innerText = "Camera permission required.";
        });
    </script>
    </body>
    </html>
    """

    components.html(qr_html, height=450, width=600)

# ---------------------------
# Main Page
# ---------------------------
def main():
    st.markdown("<h1 style='text-align:center; color:#FFD700;'>QR Attendance Scanner</h1>", unsafe_allow_html=True)

    # hidden input to receive scanned QR
    if "scanned" not in st.session_state:
        st.session_state.scanned = ""

    qr_scanner()

    # JS to receive postMessage
    components.html("""
    <script>
    window.addEventListener("message", (event) => {
        if (event.data.type === "qr") {
            // send to streamlit
            window.parent.postMessage({ type: 'qr_to_streamlit', text: event.data.text }, "*");
        }
    }, false);
    </script>
    """, height=0)

    # Update session_state with QR (this part works)
    qr = st.experimental_get_query_params().get("qr", [""])[0]

    # Use hidden text_input to trigger Streamlit rerun
    st.text_input("scanned_qr", key="scanned", value=qr, label_visibility="collapsed")

    if st.session_state.scanned:
        scanned = st.session_state.scanned
        st.session_state.scanned = ""

        parts = scanned.split("|")
        if len(parts) != 2:
            st.error("Invalid QR format. Use: Name | EmpID")
            return

        name_qr = parts[0].strip()
        emp_id = parts[1].strip()

        df_employees = read_employee_file()
        if df_employees is None:
            return

        # verify
        if emp_id in df_employees["emp"].astype(str).tolist():
            name = df_employees[df_employees["emp"].astype(str) == emp_id]["name"].values[0]

            st.success(f"VERIFIED: {name} | {emp_id}")

            df_att = load_attendance()
            today = datetime.date.today().strftime("%Y-%m-%d")

            # prevent duplicate attendance for same day
            if ((df_att["emp_id"].astype(str) == emp_id) & (df_att["date"] == today)).any():
                st.warning("Attendance already recorded today.")
            else:
                df_att = df_att.append({
                    "name": name,
                    "emp_id": emp_id,
                    "date": today,
                    "time": datetime.datetime.now().strftime("%H:%M:%S")
                }, ignore_index=True)
                save_attendance(df_att)
                st.success(f"Attendance recorded for {name} ({emp_id})")

        else:
            st.error("Employee NOT VERIFIED ❌")

    st.markdown("---")
    st.markdown("<h2 style='color:#FFD700;'>Verified Attendance Logs</h2>", unsafe_allow_html=True)
    st.dataframe(load_attendance())

if __name__ == "__main__":
    main()
