import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import uuid
import io
import os
from datetime import datetime

# --- 1. DATABASE & STRUCTURE ---
DATABASE_NAME = 'jmi_global_v6_6.db'
conn = sqlite3.connect(DATABASE_NAME, check_same_thread=False)
c = conn.cursor()

def init_db():
    c.execute('CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, grade TEXT, reg_date TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, amount REAL, date TEXT, staff_name TEXT, transaction_id TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS attendance (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, status TEXT, date TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS skill_passport (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, skill_name TEXT, date_achieved TEXT)')
    # Updated Health Table for BMI
    c.execute('CREATE TABLE IF NOT EXISTS health_tracker (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, weight REAL, height REAL, bmi REAL, status TEXT, date TEXT)')
    # New Table for Assignments (LMS - Point 1)
    c.execute('CREATE TABLE IF NOT EXISTS assignments (id INTEGER PRIMARY KEY AUTOINCREMENT, grade TEXT, title TEXT, deadline TEXT, link TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS inventory (id INTEGER PRIMARY KEY AUTOINCREMENT, item_name TEXT, stock INTEGER, price REAL)')
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)')
    
    admin_hash = hashlib.sha256(str.encode("JMI@2026")).hexdigest()
    c.execute("INSERT OR IGNORE INTO users VALUES (?,?,?)", ('admin', admin_hash, 'Owner'))
    conn.commit()

init_db()

# --- 2. BMI CALCULATOR LOGIC (Point 4) ---
def calculate_bmi(w, h):
    if h > 0:
        bmi_val = round(w / ((h/100)**2), 2)
        if bmi_val < 18.5: status = "Underweight"
        elif 18.5 <= bmi_val <= 24.9: status = "Healthy"
        else: status = "Overweight"
        return bmi_val, status
    return 0, "N/A"

# --- 3. UI STYLING ---
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
    div[data-testid="stMetricValue"] { color: #D4AF37 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. AUTHENTICATION ---
if 'auth' not in st.session_state: st.session_state['auth'] = False

# Sidebar Branding
if os.path.exists("logo.png"): st.sidebar.image("logo.png", use_container_width=True)
else: st.sidebar.markdown("<h1 style='text-align:center; color:#D4AF37;'>JMI</h1>", unsafe_allow_html=True)

if not st.session_state['auth']:
    st.sidebar.title("ACCESS PORTAL")
    u = st.sidebar.text_input("Username")
    p = st.sidebar.text_input("Password", type='password')
    role_login = st.sidebar.selectbox("Login as", ["Admin/Staff", "Parent/Student"])
    
    if st.sidebar.button("ENTER SYSTEM"):
        if role_login == "Admin/Staff":
            input_hash = hashlib.sha256(str.encode(p)).hexdigest()
            res = c.execute("SELECT password, role FROM users WHERE username=?", (u,)).fetchone()
            if res and input_hash == res[0]:
                st.session_state.update({"auth": True, "user": u, "role": "Owner"})
                st.rerun()
            else: st.sidebar.error("Invalid Admin Credentials")
        else:
            # Simple Parent Access (Username is Student Name, Password is 'JMI2026')
            if p == "JMI2026":
                st.session_state.update({"auth": True, "user": u, "role": "Parent"})
                st.rerun()
            else: st.sidebar.error("Parent Code Incorrect")
else:
    st.sidebar.success(f"Logged in: {st.session_state['user']}")
    if st.sidebar.button("LOGOUT"):
        st.session_state['auth'] = False
        st.rerun()

# --- 5. MAIN SYSTEM ---
if st.session_state['auth']:
    role = st.session_state['role']
    st.title(f"🏛️ JMI MASTER SYSTEM v6.6")

    # Dynamic Tabs based on Role (Point 2)
    if role == "Owner":
        menu = ["📝 Enrollment", "💰 Payments", "📅 Attendance", "📜 Skill Passport", "🧬 LMS & Assignments", "🍎 Health/BMI", "🛒 Inventory", "👤 360 Search", "📊 CEO Dashboard"]
    else:
        menu = ["👤 My Child Profile", "📜 My Skills", "📅 My Attendance", "🧬 Homework/LMS", "🍎 Health Report"]
    
    tabs = st.tabs(menu)
    students_master = pd.read_sql_query("SELECT id, name, grade FROM students", conn)

    # --- ADMIN VIEW LOGIC ---
    if role == "Owner":
        # (Enrollment & Payments omitted for brevity - same as v6.5)
        with tabs[0]: st.header("Enrollment Portal"); # [Insert Enrollment Form from v6.5]
        with tabs[1]: st.header("Tuition Fees"); # [Insert Payment Form from v6.5]
        
        # TAB 4: SKILL PASSPORT
        with tabs[3]:
            st.header("Issue Certification")
            if not students_master.empty:
                sid = st.selectbox("Select Student", students_master['id'], format_func=lambda x: students_master[students_master['id']==x]['name'].values[0], key="sk_sid")
                sk = st.text_input("Skill Achieved")
                if st.button("CERTIFY"):
                    c.execute("INSERT INTO skill_passport (student_id, skill_name, date_achieved) VALUES (?,?,?)", (sid, sk, datetime.now().strftime("%Y-%m-%d")))
                    conn.commit(); st.success("Certified!")
            st.dataframe(pd.read_sql_query("SELECT students.name, skill_name, date_achieved FROM skill_passport JOIN students ON skill_passport.student_id = students.id", conn))

        # TAB 5: LMS & ASSIGNMENTS (Point 1)
        with tabs[4]:
            st.header("LMS: Assignment Manager")
            with st.form("lms_form"):
                l_grade = st.selectbox("Assign to Grade", ["K1-K4", "P1-P6", "S1-S3", "H1-H3"])
                l_title = st.text_input("Assignment Title")
                l_date = st.date_input("Deadline")
                l_link = st.text_input("Resource/Submission Link")
                if st.form_submit_button("PUBLISH TO STUDENTS"):
                    c.execute("INSERT INTO assignments (grade, title, deadline, link) VALUES (?,?,?,?)", (l_grade, l_title, str(l_date), l_link))
                    conn.commit(); st.success("Homework Published!")
            st.subheader("Active Homework")
            st.dataframe(pd.read_sql_query("SELECT * FROM assignments", conn))

        # TAB 6: HEALTH & BMI (Point 4)
        with tabs[5]:
            st.header("Health Analytics (BMI)")
            if not students_master.empty:
                sid_h = st.selectbox("Student", students_master['id'], format_func=lambda x: students_master[students_master['id']==x]['name'].values[0], key="h_sid")
                col_w, col_h = st.columns(2)
                w = col_w.number_input("Weight (kg)")
                h = col_h.number_input("Height (cm)")
                if st.button("CALCULATE & LOG"):
                    bmi, status = calculate_bmi(w, h)
                    c.execute("INSERT INTO health_tracker (student_id, weight, height, bmi, status, date) VALUES (?,?,?,?,?,?)", (sid_h, w, h, bmi, status, datetime.now().strftime("%Y-%m-%d")))
                    conn.commit()
                    st.success(f"BMI: {bmi} | Status: {status}")
            st.dataframe(pd.read_sql_query("SELECT students.name, weight, height, bmi, status, date FROM health_tracker JOIN students ON health_tracker.student_id = students.id", conn))

    # --- PARENT VIEW LOGIC (Point 2) ---
    else:
        child_name = st.session_state['user']
        child_data = students_master[students_master['name'] == child_name]
        
        if child_data.empty:
            st.error("Child name not found. Please contact administration.")
        else:
            cid = int(child_data['id'].values[0])
            with tabs[0]:
                st.header(f"Welcome to {child_name}'s Portal")
                st.metric("Current Grade", child_data['grade'].values[0])
            with tabs[1]:
                st.header("Achieved Medical Skills")
                st.table(pd.read_sql_query(f"SELECT skill_name, date_achieved FROM skill_passport WHERE student_id={cid}", conn))
            with tabs[3]:
                st.header("Homework & Resources")
                st.dataframe(pd.read_sql_query(f"SELECT title, deadline, link FROM assignments WHERE grade='{child_data['grade'].values[0]}'", conn))
            with tabs[4]:
                st.header("Health Report")
                st.dataframe(pd.read_sql_query(f"SELECT weight, height, bmi, status, date FROM health_tracker WHERE student_id={cid}", conn))

st.markdown(f"<div class='footer'><b>Prepared by Dr. CHAN Sokhoeurn, C2/DBA</b> | JMI International Standard v6.6 | 2026</div>", unsafe_allow_html=True)
