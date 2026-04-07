import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import uuid
import requests
import random
import io
from datetime import datetime

# --- 1. DATABASE & USER TABLE CONFIGURATION ---
conn = sqlite3.connect('jmi_secure_v3.db', check_same_thread=False)
c = conn.cursor()

def init_db():
    # Tables for Students, Payments, and Logs
    c.execute('''CREATE TABLE IF NOT EXISTS students 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, grade TEXT, reg_date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS payments 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, amount REAL, 
                  date TEXT, staff_name TEXT, transaction_id TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS activity_logs 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, action TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    
    # Table for User Roles and Passwords
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT, role TEXT)''')
    
    # Pre-configure User Accounts (Hashing passwords for security)
    users_data = [
        ('admin', hashlib.sha256(str.encode("JMI@2026")).hexdigest(), 'Owner'),
        ('frontdesk', hashlib.sha256(str.encode("JMI_Staff_FD")).hexdigest(), 'Front Desk'),
        ('academic', hashlib.sha256(str.encode("JMI_Staff_AC")).hexdigest(), 'Academic')
    ]
    try:
        c.executemany("INSERT OR IGNORE INTO users VALUES (?,?,?)", users_data)
    except: pass
    conn.commit()

init_db()

# --- 2. SECURITY CONFIGURATION ---
TELEGRAM_TOKEN = "YOUR_BOT_TOKEN_HERE"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID_HERE"

def check_hashes(password, hashed_text):
    return hashlib.sha256(str.encode(password)).hexdigest() == hashed_text

def send_telegram_otp(otp_code):
    message = f"🔐 JMI SECURITY ALERT: Your CEO 2FA code is: {otp_code}"
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage?chat_id={TELEGRAM_CHAT_ID}&text={message}"
    try: requests.get(url)
    except: st.error("Telegram Connection Failed")

# --- 3. UI BRANDING ---
st.set_page_config(page_title="JMI System | CHAN Sokhoeurn", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    [data-testid="stSidebar"] { background-color: #000080; color: white; }
    .stButton>button { background-color: #000080; color: #FFD700; border-radius: 8px; font-weight: bold; width: 100%; }
    .footer { position: fixed; bottom: 0; left: 0; width: 100%; background: white; text-align: center; padding: 10px; font-size: 12px; color: #666; border-top: 1px solid #ddd; z-index: 100; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. SECURE LOGIN SYSTEM ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

st.sidebar.title("🔐 JMI SYSTEM ACCESS")
if not st.session_state['logged_in']:
    u_input = st.sidebar.text_input("Username")
    p_input = st.sidebar.text_input("Password", type='password')
    if st.sidebar.button("LOGIN"):
        user_record = c.execute("SELECT password, role FROM users WHERE username=?", (u_input,)).fetchone()
        if user_record and check_hashes(p_input, user_record[0]):
            st.session_state['logged_in'] = True
            st.session_state['user'] = u_input
            st.session_state['role'] = user_record[1]
            st.rerun()
        else:
            st.sidebar.error("Invalid Username or Password")
else:
    st.sidebar.success(f"Loged in as: {st.session_state['role']}")
    if st.sidebar.button("LOGOUT"):
        st.session_state['logged_in'] = False
        st.rerun()

# --- 5. ROLE-BASED DASHBOARD ---
if st.session_state['logged_in']:
    role = st.session_state['role']

    # --- FRONT DESK MODULE ---
    if role in ["Owner", "Front Desk"]:
        st.header("🏢 Front Desk Operations")
        t1, t2 = st.tabs(["Student Registration", "Payments"])
        with t1:
            with st.form("reg"):
                name = st.text_input("Student Name")
                grade = st.selectbox("Level", ["Flyers Master", "C2 Mastery"])
                if st.form_submit_button("Submit"):
                    c.execute("INSERT INTO students (name, grade, reg_date) VALUES (?,?,?)", (name, grade, datetime.now().strftime("%Y-%m-%d")))
                    conn.commit()
                    st.success("Student Saved.")
        with t2:
            st.subheader("Collect Payment")
            st_list = pd.read_sql_query("SELECT id, name FROM students", conn)
            if not st_list.empty:
                sid = st.selectbox("Student", st_list['id'], format_func=lambda x: st_list[st_list['id']==x]['name'].values[0])
                val = st.number_input("Amount ($)", min_value=0.0)
                if st.button("Confirm TX"):
                    tx = str(uuid.uuid4())[:8].upper()
                    c.execute("INSERT INTO payments (student_id, amount, date, staff_name, transaction_id) VALUES (?,?,?,?,?)", 
                              (int(sid), val, datetime.now().strftime("%Y-%m-%d %H:%M"), st.session_state['user'], tx))
                    conn.commit()
                    st.success(f"Paid! TX: {tx}")

    # --- ACADEMIC MODULE ---
    if role in ["Owner", "Academic"]:
        st.header("🎓 Academic Management")
        df_s = pd.read_sql_query("SELECT * FROM students", conn)
        st.write("Student Roster:")
        st.dataframe(df_s, use_container_width=True)

    # --- OWNER DASHBOARD ---
    if role == "Owner":
        st.markdown("---")
        st.header("📊 CEO Master Panel")
        rev = c.execute("SELECT SUM(amount) FROM payments").fetchone()[0] or 0
        st.metric("Total Revenue", f"${rev:,.2f}")
        
        # 2FA for Export
        if st.button("Generate 2FA for Excel Export"):
            otp = random.randint(100000, 999999)
            st.session_state.otp = str(otp)
            send_telegram_otp(otp)
            st.info("OTP Sent to CEO Telegram.")
        
        check_otp = st.text_input("Verify OTP", type="password")
        if check_otp == st.session_state.get('otp'):
            st.success("Verification Passed.")
            data = pd.read_sql_query("SELECT * FROM payments", conn)
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine='xlsxwriter') as wr:
                data.to_excel(wr, index=False)
            st.download_button("Download Financial Report", data=buf, file_name="JMI_Finance.xlsx")

# --- FOOTER ---
st.markdown(f"<div class='footer'>Prepared by <b>CHAN Sokhoeurn, C2/DBA</b></div>", unsafe_allow_html=True)
