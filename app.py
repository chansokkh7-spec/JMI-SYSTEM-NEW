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
# Database version 5.4: Comprehensive JMI Path (K1-K4, P1-P6, S1-S3, H1-H3, PUF1-PUF2)
conn = sqlite3.connect('jmi_final_v5_4.db', check_same_thread=False)
c = conn.cursor()

def init_db():
    c.execute('''CREATE TABLE IF NOT EXISTS students 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, grade TEXT, reg_date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS payments 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, amount REAL, 
                  date TEXT, staff_name TEXT, transaction_id TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS activity_logs 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, action TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT, role TEXT)''')
    
    # Default Accounts
    default_users = [
        ('admin', hashlib.sha256(str.encode("JMI@2026")).hexdigest(), 'Owner'),
        ('frontdesk', hashlib.sha256(str.encode("JMI_Staff_FD")).hexdigest(), 'Front Desk'),
        ('academic', hashlib.sha256(str.encode("JMI_Staff_AC")).hexdigest(), 'Academic')
    ]
    c.executemany("INSERT OR IGNORE INTO users VALUES (?,?,?)", default_users)
    conn.commit()

init_db()

# --- 2. CONFIGURATION ---
TELEGRAM_TOKEN = "YOUR_BOT_TOKEN_HERE"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID_HERE"

def check_hashes(password, hashed_text):
    return hashlib.sha256(str.encode(password)).hexdigest() == hashed_text

def send_telegram_otp(otp_code):
    message = f"🔐 JMI SECURITY ALERT: Your 2FA Code is: {otp_code}."
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage?chat_id={TELEGRAM_CHAT_ID}&text={message}"
    try: requests.get(url)
    except: st.error("Telegram Connection Error")

# --- 3. PREMIUM UI BRANDING ---
st.set_page_config(page_title="JMI Portal | CHAN Sokhoeurn", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #fcfcfc; }
    [data-testid="stSidebar"] { background-color: #000080; color: white; border-right: 4px solid #FFD700; }
    .stButton>button { background-color: #000080; color: #FFD700; border: 1px solid #FFD700; border-radius: 10px; font-weight: bold; width: 100%; }
    h1, h2, h3 { color: #000080; border-bottom: 2px solid #FFD700; padding-bottom: 5px; }
    .footer { position: fixed; bottom: 0; left: 0; width: 100%; background: white; text-align: center; padding: 10px; font-size: 13px; color: #333; border-top: 2px solid #FFD700; z-index: 100; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. AUTHENTICATION ---
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
            st.sidebar.error("Invalid Credentials")
else:
    st.sidebar.write(f"👤 User: **{st.session_state['user']}**")
    if st.sidebar.button("LOGOUT"):
        st.session_state['auth'] = False
        st.rerun()

# --- 5. FUNCTIONAL MODULES ---
if st.session_state['auth']:
    role = st.session_state['role']

    if role in ["Owner", "Front Desk"]:
        st.header("🏢 Front Desk Operations")
        tab1, tab2 = st.tabs(["New Enrollment", "Payment Collection"])
        
        with tab1:
            with st.form("enroll_form"):
                st_name = st.text_input("Student Full Name")
                
                # REVISED JMI PROGRAM PATHWAY
                program_options = [
                    "-- JMI KINDERGARTEN (9 Lessons) --",
                    "K1: Little Explorers (Body & Hygiene)",
                    "K2: Health Heroes (Organs & Germs)",
                    "K3: Junior Medics (Medical Tools)",
                    "K4: Little Specialists (Brain & Pre-Science)",
                    "-- JMI PRIMARY (12 Lessons) --",
                    "P1 & P2: Foundational Human Biology",
                    "P3 & P4: Preventive Medicine",
                    "P5 & P6: Clinical Skills & First Aid",
                    "-- JMI SECONDARY (15 Lessons) --",
                    "S1: Advanced Human Biology",
                    "S2: Pathology & Prevention",
                    "S3: Clinical Skills & Ethics",
                    "-- JMI HIGH SCHOOL (19 Lessons) --",
                    "H1: Medical Science Foundation",
                    "H2: Advanced Clinical Path",
                    "H3: Pre-Med Research & Leadership",
                    "-- JMI UNIVERSITY PREP (21 Lessons) --",
                    "PUF 1: Pre-University Foundation Level 1",
                    "PUF 2: Pre-University Foundation Level 2"
                ]
                st_level = st.selectbox("Select JMI Program Path", program_options)
                
                # Contextual Guidance for Staff
                if st_level.startswith("K"):
                    st.info("🎯 Focus: Basic hygiene, body awareness, and medical curiosity.")
                elif st_level.startswith("P"):
                    st.info("🎯 Focus: Biological systems, nutrition, and basic first aid skills.")
                elif st_level.startswith("S"):
                    st.info("🎯 Focus: Advanced human science, pathology, and medical ethics.")
                elif st_level.startswith("H"):
                    st.info("🎯 Focus: Clinical research, leadership, and high-level medical theory.")
                elif st_level.startswith("PUF"):
                    st.info("🎯 Focus: Direct preparation for Medical School entrance and advanced sciences.")

                if st.form_submit_button("REGISTER STUDENT"):
                    if st_name and not st_level.startswith("--"):
                        c.execute("INSERT INTO students (name, grade, reg_date) VALUES (?,?,?)", 
                                  (st_name, st_level, datetime.now().strftime("%Y-%m-%d")))
                        c.execute("INSERT INTO activity_logs (user, action) VALUES (?,?)", 
                                  (st.session_state['user'], f"Registered: {st_name} to {st_level}"))
                        conn.commit()
                        st.success(f"✅ Success! {st_name} is enrolled in {st_level}")
                    else: st.warning("Please enter student name and select a valid program.")

        with tab2:
            st.subheader("Payment Management")
            st_list = pd.read_sql_query("SELECT id, name FROM students", conn)
            if not st_list.empty:
                sel_id = st.selectbox("Select Student", st_list['id'], format_func=lambda x: st_list[st_list['id']==x]['name'].values[0])
                amt = st.number_input("Amount Collected ($)", min_value=0.0)
                if st.button("ISSUE RECEIPT"):
                    tx = str(uuid.uuid4())[:8].upper()
                    c.execute("INSERT INTO payments (student_id, amount, date, staff_name, transaction_id) VALUES (?,?,?,?,?)",
                              (int(sel_id), amt, datetime.now().strftime("%Y-%m-%d %H:%M"), st.session_state['user'], tx))
                    conn.commit()
                    st.success(f"Transaction Recorded: {tx}")

    if role in ["Owner", "Academic"]:
        st.header("🎓 Academic Records")
        records = pd.read_sql_query("SELECT * FROM students", conn)
        st.dataframe(records, use_container_width=True)

    if role == "Owner":
        st.markdown("---")
        st.header("📊 CEO Master Dashboard")
        revenue = c.execute("SELECT SUM(amount) FROM payments").fetchone()[0] or 0
        students_count = c.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        col1, col2 = st.columns(2)
        col1.metric("Total Revenue", f"${revenue:,.2f}")
        col2.metric("Active JMI Students", students_count)

        # 2FA Data Export
        st.subheader("📥 Data Export Center (2FA)")
        if 'verified' not in st.session_state: st.session_state.verified = False
        if not st.session_state.verified:
            if st.button("Get OTP via Telegram"):
                otp = random.randint(100000, 999999)
                st.session_state.otp_code = str(otp)
                send_telegram_otp(otp)
                st.info("Verification code sent to Telegram.")
            otp_in = st.text_input("Enter Code", type="password")
            if otp_in == st.session_state.get('otp_code'):
                st.session_state.verified = True
                st.rerun()
        else:
            data = pd.read_sql_query("SELECT * FROM payments", conn)
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine='xlsxwriter') as wr:
                data.to_excel(wr, index=False)
            st.download_button("DOWNLOAD MASTER EXCEL", data=buf, file_name=f"JMI_Report_{datetime.now().strftime('%Y%m%d')}.xlsx")
            if st.button("RESET LOCK"):
                st.session_state.verified = False
                st.rerun()

        # User Management
        st.markdown("---")
        st.subheader("👥 System User Accounts")
        with st.expander("Add New Account"):
            nu, np = st.text_input("Username"), st.text_input("Password", type="password")
            nr = st.selectbox("Role", ["Front Desk", "Academic", "Owner"])
            if st.button("CREATE ACCOUNT"):
                if nu and np:
                    hashed = hashlib.sha256(str.encode(np)).hexdigest()
                    try:
                        c.execute("INSERT INTO users VALUES (?,?,?)", (nu, hashed, nr))
                        conn.commit()
                        st.success(f"User {nu} created.")
                    except: st.error("User already exists.")
        st.table(pd.read_sql_query("SELECT username, role FROM users", conn))

st.markdown(f"<div class='footer'><b>Prepared by CHAN Sokhoeurn, C2/DBA</b> | JMI Secure Ecosystem v5.4 | 2026 </div>", unsafe_allow_html=True)
