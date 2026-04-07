import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import uuid
import io
from datetime import datetime

# --- 1. DATABASE INITIALIZATION ---
conn = sqlite3.connect('jmi_ultra_v5_8.db', check_same_thread=False)
c = conn.cursor()

def init_db():
    c.execute('CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, grade TEXT, reg_date TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, amount REAL, date TEXT, staff_name TEXT, transaction_id TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS attendance (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, status TEXT, date TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)')
    
    admin_hash = hashlib.sha256(str.encode("JMI@2026")).hexdigest()
    c.execute("INSERT OR IGNORE INTO users VALUES (?,?,?)", ('admin', admin_hash, 'Owner'))
    conn.commit()

init_db()

# --- 2. THEME & STYLE ---
st.set_page_config(page_title="JMI Portal | CHAN Sokhoeurn", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #000033; }
    [data-testid="stSidebar"] { background-color: #00001a !important; border-right: 2px solid #D4AF37; }
    h1, h2, h3, label, p, span, .stMarkdown { color: #D4AF37 !important; }
    .stButton>button { background-color: #D4AF37; color: #000033; border-radius: 8px; font-weight: bold; border: 1px solid #FFD700; }
    .stTabs [data-baseweb="tab"] { color: #D4AF37 !important; font-size: 16px; }
    .footer { position: fixed; bottom: 0; left: 0; width: 100%; background-color: #00001a; text-align: center; padding: 5px; color: #D4AF37; border-top: 1px solid #D4AF37; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. AUTHENTICATION ---
if 'auth' not in st.session_state: st.session_state['auth'] = False

if not st.session_state['auth']:
    st.sidebar.title("JMI LOGIN")
    u, p = st.sidebar.text_input("User"), st.sidebar.text_input("Pass", type='password')
    if st.sidebar.button("LOGIN"):
        res = c.execute("SELECT password, role FROM users WHERE username=?", (u,)).fetchone()
        if res and hashlib.sha256(str.encode(p)).hexdigest() == res[0]:
            st.session_state.update({"auth": True, "user": u, "role": res[1]})
            st.rerun()
else:
    if st.sidebar.button("LOGOUT"):
        st.session_state['auth'] = False
        st.rerun()

# --- 4. MAIN SYSTEM ---
if st.session_state.get('auth'):
    role = st.session_state['role']
    st.title(f"🏛️ JMI MASTER SYSTEM (Role: {role})")

    # Define Tabs based on Role
    if role == "Owner":
        tabs = st.tabs(["📝 Enrollment", "💰 Payments", "📅 Attendance", "📊 CEO Dashboard", "⚙️ Admin Control"])
    else:
        tabs = st.tabs(["📝 Enrollment", "💰 Payments", "📅 Attendance"])

    # --- TAB 1: ENROLLMENT ---
    with tabs[0]:
        st.header("Registration")
        with st.form("reg"):
            n = st.text_input("Student Full Name")
            g = st.selectbox("Grade", ["K1-K4", "P1-P6", "S1-S3", "H1-H3", "PUF1-PUF2"])
            if st.form_submit_button("SUBMIT"):
                c.execute("INSERT INTO students (name, grade, reg_date) VALUES (?,?,?)", (n, g, datetime.now().strftime("%Y-%m-%d")))
                conn.commit()
                st.success(f"{n} Registered!")

    # --- TAB 2: PAYMENTS ---
    with tabs[1]:
        st.header("Financial Collection")
        sts = pd.read_sql_query("SELECT id, name FROM students", conn)
        if not sts.empty:
            sid = st.selectbox("Select Student", sts['id'], format_func=lambda x: sts[sts['id']==x]['name'].values[0])
            amt = st.number_input("Amount ($)", min_value=0.0)
            if st.button("COLLECT"):
                tid = str(uuid.uuid4())[:8].upper()
                c.execute("INSERT INTO payments (student_id, amount, date, staff_name, transaction_id) VALUES (?,?,?,?,?)",
                          (int(sid), amt, datetime.now().strftime("%Y-%m-%d"), st.session_state['user'], tid))
                conn.commit()
                st.info(f"Receipt ID: {tid}")

    # --- TAB 3: ATTENDANCE ---
    with tabs[2]:
        st.header("Daily Attendance")
        date_today = datetime.now().strftime("%Y-%m-%d")
        st_data = pd.read_sql_query("SELECT id, name FROM students", conn)
        for index, row in st_data.iterrows():
            col_n, col_s = st.columns([3, 1])
            col_n.write(f"ID: {row['id']} | **{row['name']}**")
            status = col_s.radio("Status", ["Present", "Absent"], key=f"att_{row['id']}")
            if st.button(f"Save Attendance for ID {row['id']}", key=f"btn_{row['id']}"):
                c.execute("INSERT INTO attendance (student_id, status, date) VALUES (?,?,?)", (row['id'], status, date_today))
                conn.commit()
                st.toast(f"Saved: {row['name']} is {status}")

    # --- TAB 4: CEO DASHBOARD (Owner Only) ---
    if role == "Owner":
        with tabs[3]:
            st.header("Executive Summary")
            col1, col2 = st.columns(2)
            rev = c.execute("SELECT SUM(amount) FROM payments").fetchone()[0] or 0
            col1.metric("Total Revenue", f"${rev:,.2f}")
            col2.metric("Total Students", c.execute("SELECT COUNT(*) FROM students").fetchone()[0])
            
            st.subheader("Attendance Report Today")
            att_report = pd.read_sql_query(f"SELECT students.name, attendance.status, attendance.date FROM attendance JOIN students ON attendance.student_id = students.id WHERE attendance.date='{date_today}'", conn)
            st.table(att_report)

    # --- TAB 5: ADMIN CONTROL (Edit/Delete - Owner Only) ---
    if role == "Owner":
        with tabs[4]:
            st.header("🔐 Critical Data Management")
            
            st.subheader("Edit/Delete Payments")
            pay_df = pd.read_sql_query("SELECT * FROM payments", conn)
            st.dataframe(pay_df, use_container_width=True)
            
            del_id = st.number_input("Enter Payment ID to Delete", min_value=1, step=1)
            if st.button("DELETE PAYMENT RECORD", type="primary"):
                c.execute("DELETE FROM payments WHERE id=?", (del_id,))
                conn.commit()
                st.warning(f"Record {del_id} Deleted!")
                st.rerun()

st.markdown(f"<div class='footer'><b>Prepared by CHAN Sokhoeurn, C2/DBA</b> | JMI Secure Ecosystem v5.8</div>", unsafe_allow_html=True)
