import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import uuid
import requests
import random
import io
from datetime import datetime

# --- 1. DATABASE INITIALIZATION ---
conn = sqlite3.connect('jmi_master_v5_7.db', check_same_thread=False)
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
    
    # បង្កើតគណនី Admin លំនាំដើម ប្រសិនបើមិនទាន់មាន
    admin_hash = hashlib.sha256(str.encode("JMI@2026")).hexdigest()
    c.execute("INSERT OR IGNORE INTO users VALUES (?,?,?)", ('admin', admin_hash, 'Owner'))
    conn.commit()

init_db()

# --- 2. SECURITY FUNCTIONS ---
def check_hashes(password, hashed_text):
    return hashlib.sha256(str.encode(password)).hexdigest() == hashed_text

def log_action(user, action):
    c.execute("INSERT INTO activity_logs (user, action) VALUES (?,?)", (user, action))
    conn.commit()

# --- 3. PREMIUM NAVY & GOLD UI ---
st.set_page_config(page_title="JMI Portal | CHAN Sokhoeurn", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #000033; }
    [data-testid="stSidebar"] { background-color: #00001a !important; border-right: 2px solid #D4AF37; }
    h1, h2, h3, label, p, span, .stMarkdown { color: #D4AF37 !important; }
    .stButton>button { background-color: #D4AF37; color: #000033; border-radius: 10px; font-weight: bold; width: 100%; border: 1px solid #FFD700; }
    .stButton>button:hover { background-color: #FFD700; color: #000; }
    .stTabs [data-baseweb="tab"] { color: #D4AF37 !important; }
    .footer { position: fixed; bottom: 0; left: 0; width: 100%; background-color: #00001a; text-align: center; padding: 10px; font-size: 14px; color: #D4AF37; border-top: 1px solid #D4AF37; z-index: 100; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. LOGIN SYSTEM ---
if 'auth' not in st.session_state:
    st.session_state['auth'] = False

st.sidebar.markdown("<h1 style='text-align:center;'>JMI PORTAL</h1>", unsafe_allow_html=True)
if not st.session_state['auth']:
    u = st.sidebar.text_input("Username")
    p = st.sidebar.text_input("Password", type='password')
    if st.sidebar.button("ENTER SYSTEM"):
        res = c.execute("SELECT password, role FROM users WHERE username=?", (u,)).fetchone()
        if res and check_hashes(p, res[0]):
            st.session_state['auth'] = True
            st.session_state['user'] = u
            st.session_state['role'] = res[1]
            log_action(u, "Logged In")
            st.rerun()
        else: st.sidebar.error("Invalid Username or Password")
else:
    st.sidebar.success(f"Welcome, {st.session_state['user']} ({st.session_state['role']})")
    if st.sidebar.button("LOGOUT"):
        st.session_state['auth'] = False
        st.rerun()

# --- 5. MAIN INTERFACE ---
if st.session_state['auth']:
    role = st.session_state['role']
    
    # ការកំណត់ Tab ផ្អែកលើ Role
    # ប្រសិនបើជា Owner គាត់នឹងឃើញ Tabs ទាំងអស់
    if role == "Owner":
        tabs = st.tabs(["📝 Enrollment", "💰 Payments", "🎓 Academic Records", "📊 CEO Dashboard", "👥 User Management"])
    elif role == "Front Desk":
        tabs = st.tabs(["📝 Enrollment", "💰 Payments"])
    else: # Academic
        tabs = st.tabs(["🎓 Academic Records"])

    # --- TAB 1: ENROLLMENT ---
    if role in ["Owner", "Front Desk"]:
        with tabs[0]:
            st.header("New Student Registration")
            with st.form("enroll"):
                name = st.text_input("Full Name")
                path = st.selectbox("Program Path", [
                    "K1-K4: JMI Kindergarten", "P1-P6: JMI Primary", 
                    "S1-S3: JMI Secondary", "H1-H3: JMI High School", 
                    "PUF1-PUF2: JMI University Prep"
                ])
                if st.form_submit_button("REGISTER STUDENT"):
                    if name:
                        c.execute("INSERT INTO students (name, grade, reg_date) VALUES (?,?,?)", 
                                  (name, path, datetime.now().strftime("%Y-%m-%d")))
                        conn.commit()
                        log_action(st.session_state['user'], f"Registered Student: {name}")
                        st.success(f"Registered {name} Successfully!")

    # --- TAB 2: PAYMENTS ---
    if role in ["Owner", "Front Desk"]:
        idx = 1 if role == "Owner" else 1
        with tabs[idx]:
            st.header("Payment Collection")
            sts = pd.read_sql_query("SELECT id, name FROM students", conn)
            if not sts.empty:
                sid = st.selectbox("Select Student", sts['id'], format_func=lambda x: sts[sts['id']==x]['name'].values[0])
                amount = st.number_input("Amount ($)", min_value=0.0)
                if st.button("ISSUE RECEIPT"):
                    tid = str(uuid.uuid4())[:8].upper()
                    c.execute("INSERT INTO payments (student_id, amount, date, staff_name, transaction_id) VALUES (?,?,?,?,?)",
                              (int(sid), amount, datetime.now().strftime("%Y-%m-%d %H:%M"), st.session_state['user'], tid))
                    conn.commit()
                    log_action(st.session_state['user'], f"Collected Payment: ${amount} from ID {sid}")
                    st.success(f"Receipt Issued: {tid}")

    # --- TAB 3: ACADEMIC RECORDS ---
    if role in ["Owner", "Academic"]:
        idx = 2 if role == "Owner" else 0
        with tabs[idx]:
            st.header("Student Master Records")
            df_students = pd.read_sql_query("SELECT * FROM students", conn)
            st.dataframe(df_students, use_container_width=True)

    # --- TAB 4: CEO DASHBOARD (ONLY FOR ADMIN/OWNER) ---
    if role == "Owner":
        with tabs[3]:
            st.header("📊 Executive Overview")
            col1, col2, col3 = st.columns(3)
            total_rev = c.execute("SELECT SUM(amount) FROM payments").fetchone()[0] or 0
            total_st = c.execute("SELECT COUNT(*) FROM students").fetchone()[0]
            
            col1.metric("Total Revenue", f"${total_rev:,.2f}")
            col2.metric("Total Students", total_st)
            col3.metric("System Status", "Secure")

            st.subheader("Recent Activity Logs")
            logs = pd.read_sql_query("SELECT * FROM activity_logs ORDER BY timestamp DESC LIMIT 10", conn)
            st.table(logs)

            # Export Function
            st.subheader("📥 Data Center")
            if st.button("Generate Excel Report"):
                pay_data = pd.read_sql_query("SELECT * FROM payments", conn)
                buf = io.BytesIO()
                with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
                    pay_data.to_excel(writer, index=False)
                st.download_button("Download Report", data=buf, file_name="JMI_Financial_Report.xlsx")

    # --- TAB 5: USER MANAGEMENT (ONLY FOR ADMIN/OWNER) ---
    if role == "Owner":
        with tabs[4]:
            st.header("Manage Staff Accounts")
            with st.expander("Create New Staff Account"):
                new_u = st.text_input("New Username")
                new_p = st.text_input("New Password", type="password")
                new_r = st.selectbox("Assign Role", ["Front Desk", "Academic", "Owner"])
                if st.button("Create Account"):
                    if new_u and new_p:
                        h = hashlib.sha256(str.encode(new_p)).hexdigest()
                        try:
                            c.execute("INSERT INTO users VALUES (?,?,?)", (new_u, h, new_r))
                            conn.commit()
                            st.success(f"Account for {new_u} created!")
                        except: st.error("Username already exists!")
            
            st.subheader("Current Users")
            st.table(pd.read_sql_query("SELECT username, role FROM users", conn))

# --- 6. FOOTER ---
st.markdown(f"<div class='footer'><b>Prepared by CHAN Sokhoeurn, C2/DBA</b> | JMI Secure Master Ecosystem v5.7 | 2026</div>", unsafe_allow_html=True)
