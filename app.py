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
# Database version 5.1 includes the specialized JMI Kindergarten Curriculum
conn = sqlite3.connect('jmi_final_v5_1.db', check_same_thread=False)
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
    # Admin: JMI@2026 | Front Desk: JMI_Staff_FD | Academic: JMI_Staff_AC
    default_users = [
        ('admin', hashlib.sha256(str.encode("JMI@2026")).hexdigest(), 'Owner'),
        ('frontdesk', hashlib.sha256(str.encode("JMI_Staff_FD")).hexdigest(), 'Front Desk'),
        ('academic', hashlib.sha256(str.encode("JMI_Staff_AC")).hexdigest(), 'Academic')
    ]
    c.executemany("INSERT OR IGNORE INTO users VALUES (?,?,?)", default_users)
    conn.commit()

init_db()

# --- 2. CONFIGURATION (CEO SETTINGS) ---
# Paste your actual Bot details here to enable 2FA
TELEGRAM_TOKEN = "YOUR_BOT_TOKEN_HERE"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID_HERE"

def check_hashes(password, hashed_text):
    return hashlib.sha256(str.encode(password)).hexdigest() == hashed_text

def send_telegram_otp(otp_code):
    message = f"🔐 JMI SECURITY ALERT: Your 2FA Code for Master Export is: {otp_code}."
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage?chat_id={TELEGRAM_CHAT_ID}&text={message}"
    try: requests.get(url)
    except: st.error("Telegram Connection Error - Check Token/ID")

# --- 3. PREMIUM UI BRANDING (NAVY & GOLD) ---
st.set_page_config(page_title="JMI Secure System | Prepared by CHAN Sokhoeurn", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #fcfcfc; }
    [data-testid="stSidebar"] { background-color: #000080; color: white; border-right: 4px solid #FFD700; }
    .stButton>button { background-color: #000080; color: #FFD700; border: 1px solid #FFD700; border-radius: 10px; font-weight: bold; width: 100%; }
    h1, h2, h3 { color: #000080; border-bottom: 2px solid #FFD700; padding-bottom: 5px; }
    .footer { position: fixed; bottom: 0; left: 0; width: 100%; background: white; text-align: center; padding: 10px; font-size: 13px; color: #333; border-top: 2px solid #FFD700; z-index: 100; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. AUTHENTICATION LOGIC ---
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
            st.sidebar.error("Credentials Incorrect")
else:
    st.sidebar.write(f"👤 User: **{st.session_state['user']}**")
    st.sidebar.write(f"🏷️ Role: **{st.session_state['role']}**")
    if st.sidebar.button("LOGOUT"):
        st.session_state['auth'] = False
        st.rerun()

# --- 5. FUNCTIONAL MODULES ---
if st.session_state['auth']:
    role = st.session_state['role']

    # --- FRONT DESK MODULE (Customized JMI Curriculum) ---
    if role in ["Owner", "Front Desk"]:
        st.header("🏢 Front Desk Operations")
        tab1, tab2 = st.tabs(["New Student Enrollment", "Payment Collection"])
        
        with tab1:
            with st.form("enroll_form"):
                st_name = st.text_input("Student Full Name")
                
                # JMI SPECIALIZED PROGRAM STRUCTURE
                program_options = [
                    "K1: Little Explorers (អ្នករុករកតូច) - Body & Hygiene | 9 Lessons",
                    "K2: Health Heroes (វីរបុរសសុខភាព) - Organs & Prevention | 9 Lessons",
                    "K3: Junior Medics (គ្រូពេទ្យវ័យក្មេង) - Medical Tools | 9 Lessons",
                    "K4: Little Specialists (អ្នកឯកទេសតូច) - Brain & Science | 9 Lessons",
                    "Primary: Grade 1-6 (12 Lessons/Level)",
                    "Secondary: Grade 7-9 (15 Lessons/Level)",
                    "High School: Grade 10-12 (19 Lessons/Level)",
                    "University Prep (21 Lessons/Level)"
                ]
                st_level = st.selectbox("Select JMI Program Path", program_options)
                
                # Real-time Program Guidance for Staff
                if "K1" in st_level: st.info("Objective: Body parts, 7-step hand washing, basic hygiene.")
                elif "K2" in st_level: st.info("Objective: Internal organs (Heart, Lungs), Germs, Vitamins.")
                elif "K3" in st_level: st.info("Objective: Stethoscope, First Aid, Vaccine awareness.")
                elif "K4" in st_level: st.info("Objective: Brain function, Blood cells, Environment & Tech safety.")

                if st.form_submit_button("REGISTER STUDENT"):
                    if st_name:
                        c.execute("INSERT INTO students (name, grade, reg_date) VALUES (?,?,?)", 
                                  (st_name, st_level, datetime.now().strftime("%Y-%m-%d")))
                        c.execute("INSERT INTO activity_logs (user, action) VALUES (?,?)", 
                                  (st.session_state['user'], f"Registered: {st_name} into {st_level}"))
                        conn.commit()
                        st.success(f"✅ Successful! {st_name} is now enrolled in {st_level}")
                    else: st.warning("Please enter student name.")

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

    # --- ACADEMIC MODULE ---
    if role in ["Owner", "Academic"]:
        st.header("🎓 Academic Management")
        records = pd.read_sql_query("SELECT * FROM students", conn)
        st.dataframe(records, use_container_width=True)

    # --- OWNER DASHBOARD (CEO Master Panel) ---
    if role == "Owner":
        st.markdown("---")
        st.header("📊 CEO Master Panel (Financials & Security)")
        
        # Financial Summary
        revenue = c.execute("SELECT SUM(amount) FROM payments").fetchone()[0] or 0
        students_count = c.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        
        m1, m2 = st.columns(2)
        m1.metric("Total Revenue", f"${revenue:,.2f}")
        m2.metric("Total JMI Students", students_count)

        # 2FA Data Export Logic
        st.subheader("📥 Secure Data Export (Master Excel)")
        if 'verified' not in st.session_state: st.session_state.verified = False
        
        if not st.session_state.verified:
            if st.button("Request 2FA Code (Telegram)"):
                otp = random.randint(100000, 999999)
                st.session_state.otp_code = str(otp)
                send_telegram_otp(otp)
                st.info("Verification code sent to your private Telegram.")
            
            input_otp = st.text_input("Enter 6-Digit Code", type="password")
            if input_otp == st.session_state.get('otp_code'):
                st.session_state.verified = True
                st.rerun()
        else:
            st.success("Identity Verified. Access Granted.")
            full_data = pd.read_sql_query("SELECT * FROM payments", conn)
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                full_data.to_excel(writer, index=False)
            st.download_button("DOWNLOAD FULL FINANCIAL REPORT", data=buffer, file_name=f"JMI_Master_Report_{datetime.now().strftime('%Y%m%d')}.xlsx")
            if st.button("LOCK SECURITY"):
                st.session_state.verified = False
                st.rerun()

        # User Management for CEO
        st.markdown("---")
        st.subheader("👥 User & Staff Management")
        with st.expander("Create New Staff Account"):
            nu = st.text_input("Username")
            np = st.text_input("Password", type="password")
            nr = st.selectbox("Role", ["Front Desk", "Academic", "Owner"])
            if st.button("CREATE USER"):
                if nu and np:
                    hashed_p = hashlib.sha256(str.encode(np)).hexdigest()
                    try:
                        c.execute("INSERT INTO users VALUES (?,?,?)", (nu, hashed_p, nr))
                        conn.commit()
                        st.success(f"User {nu} created as {nr}")
                    except: st.error("Username already taken.")
        
        st.table(pd.read_sql_query("SELECT username, role FROM users", conn))

# --- 6. FOOTER ---
st.markdown(f"<div class='footer'><b>Prepared by CHAN Sokhoeurn, C2/DBA</b> | JMI Secure Ecosystem v5.1 | 2026 </div>", unsafe_allow_html=True)
