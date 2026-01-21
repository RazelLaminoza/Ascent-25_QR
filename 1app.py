import streamlit as st
import pandas as pd
import os
import base64
import datetime
import streamlit.components.v1 as components

EMPLOYEE_EXCEL = "clean_employees.xlsx"
ATTENDANCE_FILE = "attendance.csv"

# ---------------------------
# FONT + BACKGROUND
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
# DATA
# ---------------------------
def load_employees():
    if not os.path.exists(EMPLOYEE_EXCEL):
        st.error("clean_employees.xlsx not found!")
        return None
    df = pd.read_excel(EMPLOYEE_EXCEL)
    df["emp"] = df["emp"].astype(str)
    return df

def load_attendance():
    if os.path.exists(ATTENDANCE_FILE):
        return pd.read_csv(ATTENDANCE_FILE)
    return pd.DataFrame(columns=["name", "emp_id", "timestamp"])

def save_attendance(df):
    df.to_csv(ATTENDANCE_FILE, index=False)

# ---------------------------
# QR SCANNER HTML (postMessage)
# ---------------------------
def qr_scanner():
    html_code = """
    <html>
    <head>
      <script src="https://unpkg.com/html5-qrcode" type="text/javascript"></script>
    </head>
    <body>
      <div id="reader" style="width: 100%;"></div>

      <script>
        function onScanSuccess(decodedText, decodedResult) {
            window.parent.postMessage({ type: "qr", text: decodedText }, "*");
        }

        function onScanFailure(error) {}

        Html5Qrcode.getCameras().then(devices => {
          if (devices && devices.length) {
            const cameraId = devices[devices.length - 1].id; // BACK camera
            const html5Qrcode = new Html5Qrcode("reader");
            html5Qrcode.start(
              cameraId,
              { fps: 10, qrbox: 250 },
              onScanSuccess,
              onScanFailure
            );
          }
        }).catch(err => {
          document.body.innerHTML = "<h3 style='color:red; text-align:center;'>Camera permission denied</h3>";
        });
      </script>
    </body>
    </html>
    """
    components.html(html_code, height=450)

# ---------------------------
# MAIN
# ---------------------------
def main():
    st.title("QR Attendance Scanner")

    df_emp = load_employees()
    if df_emp is None:
        return

    st.subheader("Scan QR")
    qr_scanner()

    # Listen for QR message
    qr_value = st.experimental_get_query_params().get("qr", [""])[0]

    # Update session state with QR message
    if "qr_data" not in st.session_state:
        st.session_state.qr_data = ""

    # JS -> Streamlit message receiver
    st.write("""
        <script>
        window.addEventListener("message", (event) => {
            if (event.data.type === "qr") {
                const qr = event.data.text;
                window.parent.postMessage({qr: qr}, "*");
            }
        });
        </script>
    """, unsafe_allow_html=True)

    # If QR is received via message
    if st.session_state.qr_data == "":
        st.session_state.qr_data = qr_value

    if st.session_state.qr_data:
        emp_id = st.session_state.qr_data.strip()
        emp_row = df_emp[df_emp["emp"] == emp_id]

        if emp_row.empty:
            st.error("NOT VERIFIED ❌")
        else:
            name = emp_row["name"].values[0]
            df_att = load_attendance()

            if emp_id in df_att["emp_id"].astype(str).tolist():
                st.warning("Already logged today")
            else:
                df_att = df_att.append({
                    "name": name,
                    "emp_id": emp_id,
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }, ignore_index=True)
                save_attendance(df_att)
                st.success(f"Attendance logged for {name}")

        st.session_state.qr_data = ""

    st.subheader("Verified Logs")
    st.dataframe(load_attendance())

if __name__ == "__main__":
    main()
