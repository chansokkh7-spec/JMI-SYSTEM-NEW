import streamlit as st
import sqlite3
import pandas as pd
import hashlib
from datetime import datetime

# --- 1. DATABASE & UI SETUP ---
DATABASE_NAME = 'jmi_ultimate_v6_9.db'
conn = sqlite3.connect(DATABASE_NAME, check_same_thread=False)
c = conn.cursor()

def init_db():
    c.execute('CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, grade TEXT, reg_date TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, amount REAL, date TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS attendance (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, status TEXT, date TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS skill_passport (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, skill_name TEXT, date_achieved TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS health_tracker (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, weight REAL, height REAL, bmi REAL, status TEXT, date TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS assignments (id INTEGER PRIMARY KEY AUTOINCREMENT, grade TEXT, title TEXT, deadline TEXT, link TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)')
    admin_hash = hashlib.sha256(str.encode("JMI@2026")).hexdigest()
    c.execute("INSERT OR IGNORE INTO users VALUES (?,?,?)", ('admin', admin_hash, 'Owner'))
    conn.commit()

init_db()

st.set_page_config(page_title="JMI Portal | ID Generation", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #000033; }
    h1, h2, h3, p, label { color: #D4AF37 !important; }
    .id-card {
        background: linear-gradient(135deg, #00001a 0%, #000055 100%);
        border: 3px solid #D4AF37;
        border-radius: 15px;
        padding: 20px;
        width: 350px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 15px rgba(212, 175, 55, 0.3);
        margin: auto;
    }
    .id-header { font-size: 22px; font-weight: bold; color: #D4AF37; margin-bottom: 10px; border-bottom: 1px solid #D4AF37; }
    .id-body { text-align: left; margin-top: 15px; }
    .id-label { color: #D4AF37; font-size: 12px; text-transform: uppercase; }
    .id-value { font-size: 18px; font-weight: bold; margin-bottom: 8px; }
    .id-footer { font-size: 10px; margin-top: 20px; color: #aaa; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGIN SYSTEM ---
if 'auth' not in st.session_state: st.session_state['auth'] = False

if not st.session_state['auth']:
    st.sidebar.title("JMI ACCESS")
    u = st.sidebar.text_input("Username")
    p = st.sidebar.text_input("Password", type='password')
    if st.sidebar.button("LOGIN"):
        input_hash = hashlib.sha256(str.encode(p)).hexdigest()
        res = c.execute("SELECT password FROM users WHERE username=?", (u,)).fetchone()
        if res and input_hash == res[0]:
            st.session_state.update({"auth": True, "role": "Owner"})
            st.rerun()
else:
    # --- 3. MAIN DASHBOARD (Owner Mode) ---
    st.title("🏛️ JMI MASTER SYSTEM v6.9")
    tabs = st.tabs(["📝 Enrollment & ID Card", "💰 Payments", "📅 Attendance", "📜 Skills", "🧬 LMS", "🍎 Health", "📊 CEO Dashboard"])

    with tabs[0]:
        col_form, col_card = st.columns([1, 1])
        
        with col_form:
            st.header("New Registration")
            with st.form("reg_form"):
                name = st.text_input("Student Full Name")
                grade = st.selectbox("Grade Level", ["K1-K4", "P1-P6", "S1-S3", "H1-H3"])
                if st.form_submit_button("GENERATE ID CARD"):
                    if name:
                        c.execute("INSERT INTO students (name, grade, reg_date) VALUES (?,?,?)", (name, grade, datetime.now().strftime("%Y-%m-%d")))
                        conn.commit()
                        st.success(f"Student Registered Successfully!")

        with col_card:
            st.header("Digital ID Preview")
            # Fetch the latest registered student
            latest = c.execute("SELECT id, name, grade FROM students ORDER BY id DESC LIMIT 1").fetchone()
            if latest:
                st.markdown(f"""
                <div class="id-card">
                    <div class="id-header">JUNIOR MEDICAL INSTITUTE</div>
                    <div class="id-body">
                        <div class="id-label">Student Name</div>
                        <div class="id-value">{latest[1]}</div>
                        <div class="id-label">Student ID (Login Password)</div>
                        <div class="id-value">#00{latest[0]}</div>
                        <div class="id-label">Program / Grade</div>
                        <div class="id-value">{latest[2]}</div>
                    </div>
                    <div class="id-footer">
                        Prepared by Dr. CHAN Sokhoeurn, C2/DBA<br>
                        Authorized Medical Foundation School
                    </div>
                </div>
                """, unsafe_allow_html=True)
                st.info("💡 លោកបណ្ឌិតអាចចុច 'Print' (Ctrl+P) ដើម្បីព្រីនកាតនេះជូនសិស្ស។")

        st.subheader("Full Student Database")
        st.dataframe(pd.read_sql_query("SELECT id as 'ID/Password', name, grade, reg_date FROM students", conn), use_container_width=True)

    # (Other tabs logic: Payments, Attendance, Health, etc. - as perfected in v6.8)
