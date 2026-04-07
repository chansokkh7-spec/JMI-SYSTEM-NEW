import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import uuid
import requests
import random
import io
from datetime import datetime

# --- 1. DATABASE & SYSTEM INITIALIZATION ---
conn = sqlite3.connect('jmi_final_v4.db', check_same_thread=False)
c = conn.cursor()

def init_db():
    # Core Data Tables
    c.execute('''CREATE TABLE IF NOT EXISTS students 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, grade TEXT, reg_date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS payments 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, amount REAL, 
                  date TEXT, staff_name TEXT, transaction_id TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS activity_logs 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, action TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    
    # User Access Table
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT, role TEXT)''')
    
    # Pre-set Default Accounts
    # Passwords: admin -> JMI@2026 | frontdesk -> JMI_Staff_FD | academic -> JMI_Staff_AC
    default_users = [
        ('admin', hashlib.sha256(str.encode("JMI@2026")).hexdigest(), 'Owner'),
        ('frontdesk', hashlib.sha256(str.encode("JMI_Staff_FD")).hexdigest(), 'Front Desk'),
        ('academic', hashlib.sha256(str.encode("JMI_Staff_AC")).hexdigest(), 'Academic')
    ]
    c.executemany("INSERT OR IGNORE INTO users VALUES (?,?,?)", default_users)
    conn.commit()

init_db()

# --- 2. CONFIGURATION (CEO SETTINGS) ---
# Paste your Telegram details here
TELEGRAM_TOKEN = "YOUR_BOT_TOKEN_HERE"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID_HERE"

def check_hashes(password, hashed_text):
    return hashlib.sha256(str.encode(password)).hexdigest() == hashed_text

def send_telegram_otp(otp_code):
    message = f"🔐 JMI SECURITY: Your 2FA Code is: {otp_code}. Verification required for Data Export."
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage?chat_id={TELEGRAM_CHAT_ID}&text={message}"
    try: requests.get(url)
    except: st.error("Telegram Connection Error")

# --- 3. PREMIUM UI BRANDING (NAVY & GOLD) ---
st.set_page_config(page_title="JMI Secure System | CHAN Sokhoeurn", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #fcfcfc; }
    [data-testid="stSidebar"] { background-color: #000080; color: white; border-right: 3px solid #FFD700; }
    .stButton>button { background-color: #000080; color: #FFD700; border: 1px solid #FFD700; border-radius: 10px; font-weight: bold; }
    h1, h2, h3 { color: #000080; }
    .footer { position: fixed; bottom: 0; left: 0; width: 100%; background: white; text-align: center; padding: 10px; font-size: 13px; color: #333; border-top: 2px solid #FFD700; z-index: 100; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. LOGIN LOGIC ---
if 'auth' not in st.session_state:
    st.session_state['auth'] = False

st.sidebar.markdown("<h2 style='color:white; text-align:center;'>JMI PORTAL</h2>", unsafe_allow_html=True)
if not st.session_state['auth']:
    user_in = st.sidebar.text_input("Username")
    pass_in = st.sidebar.text_input("Password", type='password')
    if st.sidebar.button("ENTER SYSTEM"):
        res = c.execute("SELECT password, role FROM users WHERE username=?", (user_in,)).fetchone()
        if res and check_hashes(pass_in, res[0]):
            st.session_state['auth'] = True
            st.session_state['user'] = user_in
            st.session_state['role'] = res[1]
            st.rerun()
        else:
            st.sidebar.error("Access Denied: Credentials Incorrect")
else:
    st.sidebar.write(f"👤 User: **{st.session_state['user']}**")
    st.sidebar.write(f"🏷️ Role: **{st.session_state['role']}**")
    if st.sidebar.button("LOGOUT"):
        st.session_state['auth'] = False
        st.rerun()

# --- 5. FUNCTIONAL MODULES ---
if st.session_state['auth']:
    role = st.session_state['role']

    # --- FRONT DESK MODULE (Registration & Sales) ---
    if role in ["Owner", "Front Desk"]:
        st.header("🏢 Front Desk Operations")
        tab1, tab2 = st.tabs(["New Enrollment", "Payment Collection"])
        
        with tab1:
            with st.form("enroll"):
                st_name = st.text_input("Student Full Name")
                st_level = st.selectbox("Program", ["Basic to Master", "Flyers Master (A2)", "C2 Mastery"])
                if st.form_submit_button("Register"):
                    c.execute("INSERT INTO students (name, grade, reg_date) VALUES (?,?,?)", 
                              (st_name, st_level, datetime.now().strftime("%Y-%m-%d")))
                    c.execute("INSERT INTO activity_logs (user, action) VALUES (?,?)", (st.session_state['user'], f"Enrolled {st_name}"))
                    conn.commit()
                    st.success("Registration Successful")

        with tab2:
            st.subheader("Invoice Settlement")
            st_df = pd.read_sql_query("SELECT id, name FROM students", conn)
            if not st_df.empty:
                sel_id = st.selectbox("Select Student", st_df['id'], format_func=lambda x: st_df[st_df['id']==x]['name'].values[0])
                pay_amt = st.number_input("Amount Paid ($)", min_value=0.0)
                if st.button("Generate Receipt"):
                    tx_id = str(uuid.uuid4())[:8].upper()
                    c.execute("INSERT INTO payments (student_id, amount, date, staff_name, transaction_id) VALUES (?,?,?,?,?)",
                              (int(sel_id), pay_amt, datetime.now().strftime("%Y-%m-%d %H:%M"), st.session_state['user'], tx_id))
                    conn.commit()
                    st.success(f"Receipt Issued: {tx_id}")

    # --- ACADEMIC MODULE (Records & Lists) ---
    if role in ["Owner", "Academic"]:
        st.header("🎓 Academic Management")
        records = pd.read_sql_query("SELECT * FROM students", conn)
        st.dataframe(records, use_container_width=True)

    # --- OWNER DASHBOARD (CEO Master Panel) ---
    if role == "Owner":
        st.markdown("---")
        st.header("📊 CEO Master Panel (Financials & Security)")
        
        # Financial Metrics
        income = c.execute("SELECT SUM(amount) FROM payments").fetchone()[0] or 0
        total_s = c.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        col1, col2 = st.columns(2)
        col1.metric("Current Revenue", f"${income:,.2f}")
        col2.metric("Total Enrollment", total_s)

        # 2FA Data Export
        st.subheader("📥 Secure Data Export")
        if 'verified' not in st.session_state: st.session_state.verified = False
        
        if not st.session_state.verified:
            if st.button("Send 2FA to Telegram"):
                otp = random.randint(100000, 999999)
                st.session_state.otp_code = str(otp)
                send_telegram_otp(otp)
                st.info("Verification code sent to CEO.")
            
            check_otp = st.text_input("Enter 6-digit Security Code", type="password")
            if check_otp == st.session_state.get('otp_code'):
                st.session_state.verified = True
                st.rerun()
        else:
            st.success("Verification Passed. Data Accessible.")
            full_data = pd.read_sql_query("SELECT * FROM payments", conn)
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine='xlsxwriter') as wr:
                full_data.to_excel(wr, index=False)
            st.download_button("Download Master Excel Report", data=buf, file_name="JMI_Financial_Report.xlsx")
            if st.button("Lock Data Access"):
                st.session_state.verified = False
                st.rerun()

        # User Management Panel
        st.markdown("---")
        st.subheader("👥 User Account Management")
        with st.expander("Create New Staff Account"):
            nu = st.text_input("New Username")
            np = st.text_input("New Password", type="password")
            nr = st.selectbox("Assign Role", ["Front Desk", "Academic", "Owner"])
            if st.button("Create Account"):
                hashed = hashlib.sha256(str.encode(np)).hexdigest()
                try:
                    c.execute("INSERT INTO users VALUES (?,?,?)", (nu, hashed, nr))
                    conn.commit()
                    st.success(f"Account for {nu} created.")
                except: st.error("User already exists.")
        
        st.write("Current System Users:")
        st.table(pd.read_sql_query("SELECT username, role FROM users", conn))

# --- 6. GLOBAL FOOTER ---
st.markdown(f"<div class='footer'>Prepared by <b>CHAN Sokhoeurn, C2/DBA</b> | School Management System v4.0 (Protected)</div>", unsafe_allow_html=True)
