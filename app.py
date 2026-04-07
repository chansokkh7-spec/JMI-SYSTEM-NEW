import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import uuid
import io
import os
from datetime import datetime
from PIL import Image, ImageDraw

# --- 1. DATABASE & STRUCTURE (Checked & Verified) ---
DATABASE_NAME = 'jmi_enterprise_v7_7.db'
conn = sqlite3.connect(DATABASE_NAME, check_same_thread=False)
c = conn.cursor()

def init_db():
    # Student Profile
    c.execute('CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, grade TEXT, reg_date TEXT)')
    
    # Comprehensive Finance (Tuition, Books, Kits, Admin, Graduation)
    c.execute('''CREATE TABLE IF NOT EXISTS payments 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, fee_type TEXT, 
                  amount REAL, date TEXT, staff_name TEXT, transaction_id TEXT)''')
    
    # Academic Tracking
    c.execute('CREATE TABLE IF NOT EXISTS attendance (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, status TEXT, date TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS skill_passport (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, skill_name TEXT, date_achieved TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS health_tracker (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, weight REAL, height REAL, bmi REAL, status TEXT, date TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS assignments (id INTEGER PRIMARY KEY AUTOINCREMENT, grade TEXT, title TEXT, deadline TEXT, link TEXT)')
    
    # Inventory & Users
    c.execute('CREATE TABLE IF NOT EXISTS inventory (id INTEGER PRIMARY KEY AUTOINCREMENT, item_name TEXT, stock INTEGER, price REAL)')
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)')
    
    # Default User Roles & Passwords
    roles = [
        ('ceo_admin', 'JMI@CEO', 'Owner'),
        ('academic_prog', 'JMI@ACAD', 'Academic'),
        ('front_desk', 'JMI@FRONT', 'Front Desk'),
        ('teacher_01', 'JMI@TEACH', 'Teacher')
    ]
    for u, p, r in roles:
        p_hash = hashlib.sha256(str.encode(p)).hexdigest()
        c.execute("INSERT OR IGNORE INTO users VALUES (?,?,?)", (u, p_hash, r))
    conn.commit()

init_db()

# --- 2. CORE FUNCTIONS (BMI & ID Card) ---
def get_bmi(w, h):
    if h > 0:
        bmi = round(w / ((h/100)**2), 2)
        stat = "Healthy" if 18.5 <= bmi <= 24.9 else ("Underweight" if bmi < 18.5 else "Overweight")
        return bmi, stat
    return 0, "N/A"

def draw_id_card(name, sid, grade):
    card = Image.new('RGB', (450, 280), color='#000033')
    draw = ImageDraw.Draw(card)
    draw.rectangle([10, 10, 440, 270], outline="#D4AF37", width=4)
    draw.text((30, 30), "JUNIOR MEDICAL INSTITUTE", fill="#D4AF37")
    draw.text((30, 80), f"NAME: {name.upper()}", fill="white")
    draw.text((30, 120), f"ID: {sid}", fill="#D4AF37")
    draw.text((30, 160), f"GRADE: {grade}", fill="white")
    draw.text((30, 220), "Prepared by Dr. CHAN Sokhoeurn", fill="#D4AF37")
    buf = io.BytesIO()
    card.save(buf, format='PNG')
    return buf.getvalue()

# --- 3. PREMIUM UI STYLING (Navy & Gold) ---
st.set_page_config(page_title="JMI Master Portal", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #000033; color: white; }
    [data-testid="stSidebar"] { background-color: #00001a !important; border-right: 2px solid #D4AF37; }
    h1, h2, h3, label, p, .stMarkdown { color: #D4AF37 !important; }
    .stButton>button { background-color: #D4AF37; color: #000033; font-weight: bold; width: 100%; border-radius: 8px; }
    .stTabs [data-baseweb="tab"] { color: #D4AF37 !important; font-weight: bold; }
    .stDataFrame { border: 1px solid #D4AF37 !important; }
    input, select { background-color: #000055 !important; color: white !important; border: 1px solid #D4AF37 !important; }
    .footer { position: fixed; bottom: 0; width: 100%; text-align: center; color: #D4AF37; padding: 10px; background: #00001a; border-top: 1px solid #D4AF37; z-index: 99; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. SECURE MULTI-ROLE AUTHENTICATION ---
if 'auth' not in st.session_state: st.session_state['auth'] = False

if not st.session_state['auth']:
    st.sidebar.title("JMI ACCESS")
    user_in = st.sidebar.text_input("Username")
    pass_in = st.sidebar.text_input("Password", type='password')
    l_type = st.sidebar.selectbox("Access Mode", ["Staff/Faculty", "Parent/Student"])
    
    if st.sidebar.button("LOG IN"):
        if l_type == "Staff/Faculty":
            p_hash = hashlib.sha256(str.encode(pass_in)).hexdigest()
            res = c.execute("SELECT role FROM users WHERE username=? AND password=?", (user_in, p_hash)).fetchone()
            if res:
                st.session_state.update({"auth": True, "user": user_in, "role": res[0]})
                st.rerun()
            else: st.sidebar.error("Invalid Credentials.")
        else:
            student = c.execute("SELECT id FROM students WHERE name=? AND id=?", (user_in, pass_in)).fetchone()
            if student:
                st.session_state.update({"auth": True, "user": user_in, "role": "Parent", "sid": student[0]})
                st.rerun()
            else: st.sidebar.error("Name or ID Incorrect.")
else:
    st.sidebar.success(f"Verified: {st.session_state['role']}")
    if st.sidebar.button("LOG OUT"): st.session_state['auth'] = False; st.rerun()

# --- 5. SYSTEM MODULES ---
if st.session_state['auth']:
    role = st.session_state['role']
    st.title(f"🏛️ JMI ENTERPRISE - {role} Dashboard")
    
    # Role-Based Permissions
    menu = []
    if role == "Owner": menu = ["Enrollment", "Finance", "ID Cards", "LMS", "Skills", "Attendance", "Health", "Inventory", "CEO Dash"]
    elif role == "Front Desk": menu = ["Enrollment", "Finance", "ID Cards"]
    elif role == "Academic": menu = ["Skills", "LMS", "Health"]
    elif role == "Teacher": menu = ["Attendance", "LMS", "Health"]
    elif role == "Parent": menu = ["Personal Info", "My Skills", "Homework", "Health Vitals"]

    tabs = st.tabs(menu)
    students_df = pd.read_sql_query("SELECT * FROM students", conn)

    # --- MODULE: ENROLLMENT (Checked) ---
    if "Enrollment" in menu:
        idx = menu.index("Enrollment")
        with tabs[idx]:
            st.header("Student Registry")
            with st.form("enroll_f"):
                n = st.text_input("Full Name")
                g = st.selectbox("Grade", ["K1-K4", "P1-P6", "S1-S3", "H1-H3"])
                if st.form_submit_button("REGISTER"):
                    c.execute("INSERT INTO students (name, grade, reg_date) VALUES (?,?,?)", (n, g, datetime.now().strftime("%Y-%m-%d")))
                    conn.commit(); st.success(f"Done! Student ID: {c.lastrowid}"); st.rerun()
            st.subheader("Master List")
            st.dataframe(students_df, use_container_width=True)

    # --- MODULE: FINANCE (Verified 4 New Fee Types) ---
    if "Finance" in menu:
        idx = menu.index("Finance")
        with tabs[idx]:
            st.header("Fee Collection")
            if not students_df.empty:
                with st.form("pay_f"):
                    s_id = st.selectbox("Student", students_df['id'], format_func=lambda x: students_df[students_df['id']==x]['name'].values[0])
                    f_type = st.selectbox("Fee Type", ["Tuition Fee", "Textbook Fee (សៀវភៅ)", "Study Kit (ឯកសណ្ឋាន)", "Admin Fee (រដ្ឋបាល)", "Graduation Fee (បញ្ចប់ការសិក្សា)"])
                    amt = st.number_input("Amount ($)", min_value=0.0)
                    if st.form_submit_button("LOG PAYMENT"):
                        tid = str(uuid.uuid4())[:8].upper()
                        c.execute("INSERT INTO payments (student_id, fee_type, amount, date, staff_name, transaction_id) VALUES (?,?,?,?,?,?)", 
                                  (s_id, f_type, amt, datetime.now().strftime("%Y-%m-%d"), st.session_state['user'], tid))
                        conn.commit(); st.success(f"Receipt: {tid}")
            st.subheader("Transaction History")
            pay_log = pd.read_sql_query("SELECT p.transaction_id, s.name, p.fee_type, p.amount, p.date FROM payments p JOIN students s ON p.student_id = s.id", conn)
            st.dataframe(pay_log, use_container_width=True)

    # --- MODULE: ID CARDS (Checked) ---
    if "ID Cards" in menu:
        idx = menu.index("ID Cards")
        with tabs[idx]:
            st.header("Card Generator")
            if not students_df.empty:
                cid = st.selectbox("Select Student", students_df['id'], format_func=lambda x: students_df[students_df['id']==x]['name'].values[0], key="card_idx")
                target = students_df[students_df['id'] == cid].iloc[0]
                if st.button("CREATE DIGITAL ID"):
                    card_png = draw_id_card(target['name'], target['id'], target['grade'])
                    st.image(card_png)
                    st.download_button("📥 Download", card_png, f"JMI_{target['id']}.png", "image/png")

    # --- MODULE: LMS (Checked) ---
    if "LMS" in menu:
        idx = menu.index("LMS")
        with tabs[idx]:
            st.header("Academic LMS")
            if role in ["Owner", "Academic"]:
                with st.form("lms_f"):
                    tg = st.selectbox("Assign Grade", ["K1-K4", "P1-P6", "S1-S3", "H1-H3"])
                    tt = st.text_input("Lesson/Homework Title")
                    if st.form_submit_button("PUBLISH"):
                        c.execute("INSERT INTO assignments (grade, title, deadline) VALUES (?,?,?)", (tg, tt, datetime.now().strftime("%Y-%m-%d")))
                        conn.commit(); st.success("Task Published!")
            st.dataframe(pd.read_sql_query("SELECT * FROM assignments", conn), use_container_width=True)

    # --- MODULE: ATTENDANCE (Checked) ---
    if "Attendance" in menu:
        idx = menu.index("Attendance")
        with tabs[idx]:
            st.header("Roll Call")
            for i, r in students_df.iterrows():
                c1, c2 = st.columns([3, 1])
                c1.write(f"**{r['name']}**")
                if c2.button("MARK PRESENT", key=f"att_{r['id']}"):
                    c.execute("INSERT INTO attendance (student_id, status, date) VALUES (?,?,?)", (r['id'], "Present", datetime.now().strftime("%Y-%m-%d")))
                    conn.commit(); st.toast("Saved!")

    # --- MODULE: CEO DASHBOARD (Checked) ---
    if "CEO Dash" in menu:
        idx = menu.index("CEO Dash")
        with tabs[idx]:
            st.header("Executive Summary")
            st.metric("Total Revenue", f"${(c.execute('SELECT SUM(amount) FROM payments').fetchone()[0] or 0):,.2f}")
            st.subheader("Revenue by Category")
            rev_df = pd.read_sql_query("SELECT fee_type, SUM(amount) as Total FROM payments GROUP BY fee_type", conn)
            st.table(rev_df)

    # --- MODULE: PARENT PORTAL ---
    if role == "Parent":
        psid = st.session_state['sid']
        with tabs[0]: st.subheader(f"ID: {psid} | Name: {st.session_state['user']}")
        with tabs[1]: st.table(pd.read_sql_query(f"SELECT skill_name, date_achieved FROM skill_passport WHERE student_id={psid}", conn))
        with tabs[2]: 
            grd = c.execute("SELECT grade FROM students WHERE id=?", (psid,)).fetchone()[0]
            st.dataframe(pd.read_sql_query(f"SELECT title, deadline FROM assignments WHERE grade='{grd}'", conn))

st.markdown(f"<div class='footer'><b>Prepared by Dr. CHAN Sokhoeurn, C2/DBA</b> | JMI v7.7 | 2026</div>", unsafe_allow_html=True)
