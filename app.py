import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import uuid
import requests
import random
import io
from datetime import datetime

# --- 1. DATABASE CONFIGURATION ---
conn = sqlite3.connect('jmi_secure_v2.db', check_same_thread=False)
c = conn.cursor()

def init_db():
    c.execute('''CREATE TABLE IF NOT EXISTS students 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, grade TEXT, reg_date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS payments 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, amount REAL, 
                  date TEXT, staff_name TEXT, transaction_id TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS activity_logs 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, action TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()

init_db()

# --- 2. SECURITY & TELEGRAM CONFIGURATION ---
# Replace these with your actual Telegram Bot details
TELEGRAM_TOKEN = "YOUR_BOT_TOKEN_HERE"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID_HERE"

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    return make_hashes(password) == hashed_text

def send_telegram_otp(otp_code):
    message = f"🔐 JMI SECURITY ALERT: Your 2FA code for Data Export is: {otp_code}"
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage?chat_id={TELEGRAM_CHAT_ID}&text={message}"
    try:
        requests.get(url)
    except Exception as e:
        st.error(f"Telegram Error: {e}")

# --- 3. UI BRANDING & CSS ---
st.set_page_config(page_title="JMI System | CHAN Sokhoeurn", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f4f7f9; }
    [data-testid="stSidebar"] { background-color: #000080; color: white; }
    .stButton>button { background-color: #000080; color: #FFD700; border-radius: 8px; font-weight: bold; width: 100%; border: 1px solid #FFD700; }
    h1, h2 { color: #000080; border-bottom: 2px solid #FFD700; padding-bottom: 10px; }
    .footer { position: fixed; bottom: 0; left: 0; width: 100%; background: white; text-align: center; padding: 10px; font-size: 12px; color: #666; border-top: 1px solid #ddd; z-index: 999; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. AUTHENTICATION SYSTEM ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

st.sidebar.title("🔐 JMI SECURE ACCESS")
if not st.session_state['logged_in']:
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type='password')
    if st.sidebar.button("LOGIN"):
        # Master Password: JMI@2026
        if check_hashes(password, make_hashes("JMI@2026")):
            st.session_state['logged_in'] = True
            st.session_state['user_name'] = username
            st.rerun()
        else:
            st.sidebar.error("Invalid Credentials")
else:
    st.sidebar.success(f"User: {st.session_state['user_name']}")
    if st.sidebar.button("LOGOUT"):
        st.session_state['logged_in'] = False
        st.rerun()

# --- 5. MAIN DASHBOARD LOGIC ---
if st.session_state['logged_in']:
    menu = st.sidebar.selectbox("Navigation Menu", ["Front Desk", "Academic", "Owner Dashboard"])

    # --- MODULE: FRONT DESK ---
    if menu == "Front Desk":
        st.header("🏢 Front Desk & Enrollment")
        t1, t2 = st.tabs(["Student Registration", "Payment Processing"])
        
        with t1:
            with st.form("reg_form"):
                name = st.text_input("Full Name")
                grade = st.selectbox("Program", ["Basic to Master", "Flyers Master (A2)", "C2 Mastery"])
                if st.form_submit_button("Register Student"):
                    now = datetime.now().strftime("%Y-%m-%d")
                    c.execute("INSERT INTO students (name, grade, reg_date) VALUES (?, ?, ?)", (name, grade, now))
                    c.execute("INSERT INTO activity_logs (user, action) VALUES (?, ?)", (st.session_state['user_name'], f"Registered student: {name}"))
                    conn.commit()
                    st.success(f"Success: {name} enrolled in {grade}")

        with t2:
            st.subheader("Invoice Settlement")
            st_data = pd.read_sql_query("SELECT id, name FROM students", conn)
            if not st_data.empty:
                s_id = st.selectbox("Select Student", st_data['id'], format_func=lambda x: st_data[st_data['id']==x]['name'].values[0])
                amt = st.number_input("Amount ($)", min_value=0.0)
                if st.button("Confirm Payment"):
                    tx_id = str(uuid.uuid4())[:8].upper()
                    p_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    c.execute("INSERT INTO payments (student_id, amount, date, staff_name, transaction_id) VALUES (?, ?, ?, ?, ?)",
                              (int(s_id), amt, p_date, st.session_state['user_name'], tx_id))
                    c.execute("INSERT INTO activity_logs (user, action) VALUES (?, ?)", (st.session_state['user_name'], f"Collected ${amt} (TX: {tx_id})"))
                    conn.commit()
                    st.success(f"Transaction Complete: {tx_id}")

    # --- MODULE: ACADEMIC ---
    elif menu == "Academic":
        st.header("🎓 Academic Records")
        df_students = pd.read_sql_query("SELECT * FROM students", conn)
        st.dataframe(df_students, use_container_width=True)

    # --- MODULE: OWNER DASHBOARD (CEO/FOUNDER) ---
    elif menu == "Owner Dashboard":
        st.header("📊 Executive Analytics (CEO Only)")
        
        # Financial Summary
        revenue = c.execute("SELECT SUM(amount) FROM payments").fetchone()[0] or 0
        total_students = c.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Revenue", f"${revenue:,.2f}")
        m2.metric("Active Students", total_students)
        m3.metric("System Health", "Secure", delta="Online")

        st.markdown("---")
        st.subheader("📥 Data Export Center (2FA Protected)")
        
        if 'otp_verified' not in st.session_state:
            st.session_state.otp_verified = False

        if not st.session_state.otp_verified:
            if st.button("Send 2FA Code to Telegram"):
                otp = random.randint(100000, 999999)
                st.session_state.current_otp = str(otp)
                send_telegram_otp(otp)
                st.info("Verification code sent to CEO's Telegram.")
            
            input_otp = st.text_input("Enter 6-Digit Code", type="password")
            if input_otp == st.session_state.get('current_otp'):
                st.session_state.otp_verified = True
                st.rerun()
        else:
            st.success("Verification Successful. Access Granted.")
            query = """SELECT s.name, s.grade, p.amount, p.date, p.transaction_id FROM students s 
                       LEFT JOIN payments p ON s.id = p.student_id"""
            export_df = pd.read_sql_query(query, conn)
            
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                export_df.to_excel(writer, index=False, sheet_name='Master_Data')
            
            st.download_button(
                label="DOWNLOAD MASTER EXCEL FILE",
                data=buffer,
                file_name=f"JMI_MASTER_DATA_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.ms-excel"
            )
            
            if st.button("Reset Security Lock"):
                st.session_state.otp_verified = False
                st.rerun()

        st.subheader("📝 System Audit Logs")
        logs = pd.read_sql_query("SELECT * FROM activity_logs ORDER BY id DESC LIMIT 50", conn)
        st.table(logs)

# --- 6. FOOTER ---
st.markdown(f"""
    <div class="footer">
        System Architecture & Management by <b>CHAN Sokhoeurn, C2/DBA</b> | Confidential & Secure
    </div>
    """, unsafe_allow_html=True)
