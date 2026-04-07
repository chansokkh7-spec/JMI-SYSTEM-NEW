import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import uuid
import io
import os
from datetime import datetime

# --- 1. DATABASE ENGINE ---
DATABASE_NAME = 'jmi_international_v6_8.db'
conn = sqlite3.connect(DATABASE_NAME, check_same_thread=False)
c = conn.cursor()

def init_db():
    c.execute('CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, grade TEXT, reg_date TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, amount REAL, date TEXT, staff_name TEXT, transaction_id TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS attendance (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, status TEXT, date TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS skill_passport (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, skill_name TEXT, date_achieved TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS health_tracker (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, weight REAL, height REAL, bmi REAL, status TEXT, date TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS assignments (id INTEGER PRIMARY KEY AUTOINCREMENT, grade TEXT, title TEXT, deadline TEXT, link TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS inventory (id INTEGER PRIMARY KEY AUTOINCREMENT, item_name TEXT, stock INTEGER, price REAL)')
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)')
    
    admin_hash = hashlib.sha256(str.encode("JMI@2026")).hexdigest()
    c.execute("INSERT OR IGNORE INTO users VALUES (?,?,?)", ('admin', admin_hash, 'Owner'))
    conn.commit()

init_db()

# --- 2. UI & STYLING ---
st.set_page_config(page_title="JMI Portal | Dr. CHAN Sokhoeurn", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #000033; }
    [data-testid="stSidebar"] { background-color: #00001a !important; border-right: 2px solid #D4AF37; }
    h1, h2, h3, label, p, span, .stMarkdown { color: #D4AF37 !important; }
    .stButton>button { background-color: #D4AF37; color: #000033; border-radius: 8px; font-weight: bold; border: 1px solid #FFD700; width: 100%; }
    .stTabs [data-baseweb="tab"] { color: #D4AF37 !important; font-size: 15px; font-weight: bold; }
    .footer { position: fixed; bottom: 0; left: 0; width: 100%; background-color: #00001a; text-align: center; padding: 5px; color: #D4AF37; border-top: 1px solid #D4AF37; z-index: 100; }
    input, select, textarea { background-color: #000055 !important; color: white !important; border: 1px solid #D4AF37 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. AUTHENTICATION (New ID-Based Logic) ---
if 'auth' not in st.session_state: st.session_state['auth'] = False

if not st.session_state['auth']:
    st.sidebar.title("JMI SECURE ACCESS")
    u_input = st.sidebar.text_input("Username (Student Name / Admin)")
    p_input = st.sidebar.text_input("Password (Student ID / Admin PW)", type='password')
    mode = st.sidebar.selectbox("Role", ["CEO/Staff", "Parent/Student"])
    
    if st.sidebar.button("LOG IN"):
        if mode == "CEO/Staff":
            input_hash = hashlib.sha256(str.encode(p_input)).hexdigest()
            res = c.execute("SELECT password FROM users WHERE username=?", (u_input,)).fetchone()
            if res and input_hash == res[0]:
                st.session_state.update({"auth": True, "user": u_input, "role": "Owner"})
                st.rerun()
            else: st.sidebar.error("Invalid Admin Access")
        else:
            # Logic: Match Name and ID from students table
            student_check = c.execute("SELECT id FROM students WHERE name=? AND id=?", (u_input, p_input)).fetchone()
            if student_check:
                st.session_state.update({"auth": True, "user": u_input, "role": "Parent", "student_id": student_check[0]})
                st.rerun()
            else: st.sidebar.error("Student Name or ID incorrect")
else:
    st.sidebar.success(f"User: {st.session_state['user']}")
    if st.sidebar.button("LOG OUT"):
        st.session_state['auth'] = False
        st.rerun()

# --- 4. MAIN INTERFACE ---
if st.session_state['auth']:
    role = st.session_state['role']
    st.title("🏛️ JMI MASTER SYSTEM v6.8")
    
    # OWNER VIEW
    if role == "Owner":
        tabs = st.tabs(["📝 Enrollment", "💰 Payments", "📅 Attendance", "📜 Skill Passport", "🧬 LMS", "🍎 Health", "🛒 Inventory", "📊 CEO Dashboard"])
        
        with tabs[0]: # Enrollment with ID display
            st.header("Student Registration")
            with st.form("enroll"):
                n = st.text_input("Full Name")
                g = st.selectbox("Grade", ["K1-K4", "P1-P6", "S1-S3", "H1-H3"])
                if st.form_submit_button("REGISTER"):
                    c.execute("INSERT INTO students (name, grade, reg_date) VALUES (?,?,?)", (n, g, datetime.now().strftime("%Y-%m-%d")))
                    conn.commit(); st.success(f"Enrolled! Student ID for {n} is: {c.lastrowid}")
            st.subheader("Student Registry (ID is the Password)")
            st.dataframe(pd.read_sql_query("SELECT id, name, grade, reg_date FROM students", conn), use_container_width=True)

        # [The rest of the Admin modules: Payments, Attendance, Skill, LMS, Health, Inventory, Dashboard - exactly as v6.7]
        # (Included in full code but omitted here for clarity in explanation)

    # PARENT VIEW (Uses stored Student ID from session)
    else:
        sid = st.session_state['student_id']
        sname = st.session_state['user']
        st.header(f"Parental Portal for ID: {sid} ({sname})")
        p_tabs = st.tabs(["📜 My Skills", "📅 My Attendance", "🧬 Homework", "🍎 Health Report"])
        
        with p_tabs[0]: st.table(pd.read_sql_query(f"SELECT skill_name, date_achieved FROM skill_passport WHERE student_id={sid}", conn))
        with p_tabs[1]: st.dataframe(pd.read_sql_query(f"SELECT date, status FROM attendance WHERE student_id={sid}", conn))
        # Get Grade first
        c_grade = c.execute("SELECT grade FROM students WHERE id=?", (sid,)).fetchone()[0]
        with p_tabs[2]: st.dataframe(pd.read_sql_query(f"SELECT title, deadline, link FROM assignments WHERE grade='{c_grade}'", conn))
        with p_tabs[3]: st.dataframe(pd.read_sql_query(f"SELECT weight, height, bmi, status, date FROM health_tracker WHERE student_id={sid}", conn))

st.markdown(f"<div class='footer'><b>Prepared by Dr. CHAN Sokhoeurn, C2/DBA</b> | JMI v6.8 Security | 2026</div>", unsafe_allow_html=True)
