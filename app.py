import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import uuid
import io
import os
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

# --- 1. DATABASE ENGINE ---
DATABASE_NAME = 'jmi_ultimate_v6_9.db'
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

# --- 2. STUDENT CARD GENERATOR FUNCTION ---
def create_student_card(name, sid, grade):
    # Create a blank card with Navy Blue background
    width, height = 400, 250
    card = Image.new('RGB', (width, height), color='#000033')
    draw = ImageDraw.Draw(card)
    
    # Add Gold Border
    draw.rectangle([10, 10, 390, 240], outline="#D4AF37", width=3)
    
    # Add Text (Using default font for compatibility)
    draw.text((20, 30), "JUNIOR MEDICAL INSTITUTE", fill="#D4AF37")
    draw.text((20, 80), f"STUDENT NAME: {name.upper()}", fill="white")
    draw.text((20, 120), f"STUDENT ID: {sid}", fill="#D4AF37")
    draw.text((20, 160), f"GRADE: {grade}", fill="white")
    draw.text((20, 210), "Prepared by Dr. CHAN Sokhoeurn", fill="#D4AF37")
    
    # Save to buffer
    buf = io.BytesIO()
    card.save(buf, format='PNG')
    return buf.getvalue()

# --- 3. UI & STYLING ---
st.set_page_config(page_title="JMI Portal | Dr. CHAN Sokhoeurn", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #000033; }
    [data-testid="stSidebar"] { background-color: #00001a !important; border-right: 2px solid #D4AF37; }
    h1, h2, h3, label, p, span, .stMarkdown { color: #D4AF37 !important; }
    .stButton>button { background-color: #D4AF37; color: #000033; border-radius: 8px; font-weight: bold; border: 1px solid #FFD700; width: 100%; }
    .stTabs [data-baseweb="tab"] { color: #D4AF37 !important; font-size: 14px; font-weight: bold; }
    .footer { position: fixed; bottom: 0; left: 0; width: 100%; background-color: #00001a; text-align: center; padding: 5px; color: #D4AF37; border-top: 1px solid #D4AF37; z-index: 100; }
    input, select, textarea { background-color: #000055 !important; color: white !important; border: 1px solid #D4AF37 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. AUTHENTICATION ---
if 'auth' not in st.session_state: st.session_state['auth'] = False

if not st.session_state['auth']:
    st.sidebar.title("JMI LOGIN")
    u_in = st.sidebar.text_input("Name")
    p_in = st.sidebar.text_input("Password / Student ID", type='password')
    mode = st.sidebar.selectbox("Role", ["CEO/Staff", "Parent/Student"])
    
    if st.sidebar.button("ENTER"):
        if mode == "CEO/Staff":
            input_hash = hashlib.sha256(str.encode(p_in)).hexdigest()
            res = c.execute("SELECT password FROM users WHERE username=?", (u_in,)).fetchone()
            if res and input_hash == res[0]:
                st.session_state.update({"auth": True, "user": u_in, "role": "Owner"})
                st.rerun()
        else:
            student = c.execute("SELECT id FROM students WHERE name=? AND id=?", (u_in, p_in)).fetchone()
            if student:
                st.session_state.update({"auth": True, "user": u_in, "role": "Parent", "student_id": student[0]})
                st.rerun()
else:
    st.sidebar.success(f"User: {st.session_state['user']}")
    if st.sidebar.button("LOG OUT"): st.session_state['auth'] = False; st.rerun()

# --- 5. MAIN SYSTEM ---
if st.session_state['auth']:
    role = st.session_state['role']
    st.title("🏛️ JMI MASTER SYSTEM v6.9")
    students_master = pd.read_sql_query("SELECT id, name, grade FROM students", conn)

    if role == "Owner":
        tabs = st.tabs(["📝 Enrollment", "💰 Payments", "📅 Attendance", "📜 Skill Passport", "🧬 LMS", "🍎 Health", "🛒 Inventory", "🪪 Student Cards", "📊 Dashboard"])
        
        with tabs[0]: # Enrollment
            st.header("Student Registration")
            with st.form("enroll"):
                n = st.text_input("Full Name")
                g = st.selectbox("Grade", ["K1-K4", "P1-P6", "S1-S3", "H1-H3"])
                if st.form_submit_button("REGISTER"):
                    c.execute("INSERT INTO students (name, grade, reg_date) VALUES (?,?,?)", (n, g, datetime.now().strftime("%Y-%m-%d")))
                    conn.commit(); st.success(f"Enrolled! ID: {c.lastrowid}"); st.rerun()
            st.dataframe(students_master, use_container_width=True)

        # ... [Other tabs Payments, Attendance, Skill, LMS, Health, Inventory same as v6.8] ...
        with tabs[4]: # LMS Example
            st.header("LMS Manager")
            with st.form("lms"):
                tg = st.selectbox("Grade", ["K1-K4", "P1-P6", "S1-S3", "H1-H3"])
                tl = st.text_input("Title")
                dl = st.date_input("Deadline")
                lk = st.text_input("Link")
                if st.form_submit_button("PUBLISH"):
                    c.execute("INSERT INTO assignments (grade, title, deadline, link) VALUES (?,?,?,?)", (tg, tl, str(dl), lk))
                    conn.commit(); st.success("Published!")

        # NEW TAB: STUDENT CARDS (The functionality you requested)
        with tabs[7]:
            st.header("🪪 Student Card Center")
            if not students_master.empty:
                card_sid = st.selectbox("Select Student to Print", students_master['id'], format_func=lambda x: students_master[students_master['id']==x]['name'].values[0])
                target_student = students_master[students_master['id'] == card_sid].iloc[0]
                
                if st.button("GENERATE DIGITAL CARD"):
                    card_img = create_student_card(target_student['name'], target_student['id'], target_student['grade'])
                    st.image(card_img, caption=f"Preview for {target_student['name']}")
                    st.download_button("📥 Download Card (PNG)", card_img, f"JMI_Card_{target_student['id']}.png", "image/png")
            else: st.warning("Enroll a student first.")

        with tabs[8]: # Dashboard
            st.header("CEO Dashboard")
            m1, m2 = st.columns(2)
            m1.metric("Total Students", len(students_master))
            rev = c.execute('SELECT SUM(amount) FROM payments').fetchone()[0] or 0
            m2.metric("Total Revenue", f"${rev:,.2f}")

    # PARENT VIEW
    else:
        sid = st.session_state['student_id']
        sname = st.session_state['user']
        st.header(f"Parent Portal: {sname} (ID: {sid})")
        p_tabs = st.tabs(["📜 Skills", "📅 Attendance", "🧬 Homework", "🍎 Health"])
        with p_tabs[0]: st.table(pd.read_sql_query(f"SELECT skill_name, date_achieved FROM skill_passport WHERE student_id={sid}", conn))
        with p_tabs[1]: st.dataframe(pd.read_sql_query(f"SELECT date, status FROM attendance WHERE student_id={sid}", conn))
        # LMS for Parent
        c_grade = c.execute("SELECT grade FROM students WHERE id=?", (sid,)).fetchone()[0]
        with p_tabs[2]: st.dataframe(pd.read_sql_query(f"SELECT title, deadline, link FROM assignments WHERE grade='{c_grade}'", conn))
        with p_tabs[3]: st.dataframe(pd.read_sql_query(f"SELECT weight, height, bmi, status, date FROM health_tracker WHERE student_id={sid}", conn))

st.markdown(f"<div class='footer'><b>Prepared by Dr. CHAN Sokhoeurn, C2/DBA</b> | JMI v6.9 | 2026</div>", unsafe_allow_html=True)
