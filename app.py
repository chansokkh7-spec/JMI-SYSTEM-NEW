import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import uuid
import io
import os
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

# --- 1. DATABASE ENGINE & TABLES CONFIGURATION ---
DATABASE_NAME = 'jmi_ultimate_v7.db'
conn = sqlite3.connect(DATABASE_NAME, check_same_thread=False)
c = conn.cursor()

def init_db():
    # Students Database
    c.execute('CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, grade TEXT, reg_date TEXT)')
    # Financial Database
    c.execute('CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, amount REAL, date TEXT, staff_name TEXT, transaction_id TEXT)')
    # Attendance Database
    c.execute('CREATE TABLE IF NOT EXISTS attendance (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, status TEXT, date TEXT)')
    # Skill Passport Database
    c.execute('CREATE TABLE IF NOT EXISTS skill_passport (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, skill_name TEXT, date_achieved TEXT)')
    # Health & BMI Database
    c.execute('CREATE TABLE IF NOT EXISTS health_tracker (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, weight REAL, height REAL, bmi REAL, status TEXT, date TEXT)')
    # LMS & Assignment Database
    c.execute('CREATE TABLE IF NOT EXISTS assignments (id INTEGER PRIMARY KEY AUTOINCREMENT, grade TEXT, title TEXT, deadline TEXT, link TEXT)')
    # Inventory Database
    c.execute('CREATE TABLE IF NOT EXISTS inventory (id INTEGER PRIMARY KEY AUTOINCREMENT, item_name TEXT, stock INTEGER, price REAL)')
    # User Credentials
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)')
    
    # Default Admin (User: admin | Pass: JMI@2026)
    admin_hash = hashlib.sha256(str.encode("JMI@2026")).hexdigest()
    c.execute("INSERT OR IGNORE INTO users VALUES (?,?,?)", ('admin', admin_hash, 'Owner'))
    conn.commit()

init_db()

# --- 2. CALCULATORS & GENERATORS ---
def calculate_bmi(w, h):
    if h > 0:
        bmi = round(w / ((h/100)**2), 2)
        if bmi < 18.5: status = "Underweight"
        elif 18.5 <= bmi <= 24.9: status = "Healthy"
        else: status = "Overweight"
        return bmi, status
    return 0, "N/A"

def generate_student_card(name, sid, grade):
    width, height = 450, 280
    card = Image.new('RGB', (width, height), color='#000033') # Navy Blue
    draw = ImageDraw.Draw(card)
    # Gold Border
    draw.rectangle([10, 10, 440, 270], outline="#D4AF37", width=4)
    # Text Content
    draw.text((30, 30), "JUNIOR MEDICAL INSTITUTE", fill="#D4AF37")
    draw.text((30, 80), f"NAME: {name.upper()}", fill="white")
    draw.text((30, 120), f"STUDENT ID: {sid}", fill="#D4AF37")
    draw.text((30, 160), f"GRADE: {grade}", fill="white")
    draw.text((30, 220), "Prepared by Dr. CHAN Sokhoeurn", fill="#D4AF37")
    
    buf = io.BytesIO()
    card.save(buf, format='PNG')
    return buf.getvalue()

# --- 3. PREMIUM NAVY & GOLD UI ---
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
    .stDataFrame { border: 1px solid #D4AF37; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. LOGIN AUTHENTICATION ---
if 'auth' not in st.session_state: st.session_state['auth'] = False

if not st.session_state['auth']:
    st.sidebar.title("JMI ACCESS")
    user_in = st.sidebar.text_input("Username (Name or Admin)")
    pass_in = st.sidebar.text_input("Password (ID or Admin PW)", type='password')
    login_type = st.sidebar.selectbox("Login Mode", ["CEO/Staff", "Parent/Student"])
    
    if st.sidebar.button("LOGIN"):
        if login_type == "CEO/Staff":
            input_hash = hashlib.sha256(str.encode(pass_in)).hexdigest()
            res = c.execute("SELECT password FROM users WHERE username=?", (user_in,)).fetchone()
            if res and input_hash == res[0]:
                st.session_state.update({"auth": True, "user": user_in, "role": "Owner"})
                st.rerun()
            else: st.sidebar.error("Admin credentials incorrect.")
        else:
            student = c.execute("SELECT id FROM students WHERE name=? AND id=?", (user_in, pass_in)).fetchone()
            if student:
                st.session_state.update({"auth": True, "user": user_in, "role": "Parent", "student_id": student[0]})
                st.rerun()
            else: st.sidebar.error("Student Name or ID incorrect.")
else:
    st.sidebar.write(f"Logged as: **{st.session_state['user']}**")
    if st.sidebar.button("LOGOUT"):
        st.session_state['auth'] = False
        st.rerun()

# --- 5. MAIN SYSTEM MODULES ---
if st.session_state['auth']:
    role = st.session_state['role']
    st.title("🏛️ JMI MASTER SYSTEM v7.0")
    
    # Pre-fetching data for Tables
    students_df = pd.read_sql_query("SELECT id, name, grade, reg_date FROM students", conn)

    if role == "Owner":
        tabs = st.tabs(["📝 Enroll", "💰 Finance", "📅 Attendance", "📜 Skills", "🧬 LMS/Homework", "🍎 Health/BMI", "🛒 Stock", "🪪 ID Cards", "📊 CEO Dash"])
        
        # 📝 ENROLLMENT
        with tabs[0]:
            st.header("Student Registration")
            with st.form("enroll"):
                n = st.text_input("Full Student Name")
                g = st.selectbox("Grade Level", ["K1-K4", "P1-P6", "S1-S3", "H1-H3", "PUF1-PUF2"])
                if st.form_submit_button("SUBMIT"):
                    c.execute("INSERT INTO students (name, grade, reg_date) VALUES (?,?,?)", (n, g, datetime.now().strftime("%Y-%m-%d")))
                    conn.commit(); st.success(f"Registered {n} (ID: {c.lastrowid})"); st.rerun()
            st.subheader("Current Registry")
            st.dataframe(students_df, use_container_width=True)

        # 💰 FINANCE
        with tabs[1]:
            st.header("Payment Management")
            if not students_df.empty:
                with st.expander("Collect Tuition"):
                    sid = st.selectbox("Student", students_df['id'], format_func=lambda x: students_df[students_df['id']==x]['name'].values[0])
                    amt = st.number_input("Amount ($)", min_value=0.0)
                    if st.button("SAVE PAYMENT"):
                        tid = str(uuid.uuid4())[:8].upper()
                        c.execute("INSERT INTO payments (student_id, amount, date, staff_name, transaction_id) VALUES (?,?,?,?,?)", (sid, amt, datetime.now().strftime("%Y-%m-%d"), st.session_state['user'], tid))
                        conn.commit(); st.success(f"Receipt: {tid}")
            st.subheader("Financial Records")
            st.dataframe(pd.read_sql_query("SELECT p.id, s.name, p.amount, p.date, p.transaction_id FROM payments p JOIN students s ON p.student_id = s.id", conn), use_container_width=True)

        # 📅 ATTENDANCE
        with tabs[2]:
            st.header("Attendance Tracker")
            grade_sel = st.selectbox("Select Class", ["All", "K1-K4", "P1-P6", "S1-S3", "H1-H3"])
            list_to_mark = students_df if grade_sel == "All" else students_df[students_df['grade'] == grade_sel]
            for i, row in list_to_mark.iterrows():
                c1, c2 = st.columns([3, 1])
                c1.write(f"**{row['name']}** (ID: {row['id']})")
                stat = c2.radio("Status", ["Present", "Absent"], key=f"att_{row['id']}", horizontal=True)
                if st.button(f"Update {row['id']}", key=f"btn_{row['id']}"):
                    c.execute("INSERT INTO attendance (student_id, status, date) VALUES (?,?,?)", (row['id'], stat, datetime.now().strftime("%Y-%m-%d")))
                    conn.commit(); st.toast("Saved!")

        # 📜 SKILL PASSPORT
        with tabs[3]:
            st.header("Medical Skill Passport")
            if not students_df.empty:
                with st.expander("Issue Certification"):
                    sid_s = st.selectbox("Student", students_df['id'], format_func=lambda x: students_df[students_df['id']==x]['name'].values[0], key="sk_sid")
                    sk_val = st.text_input("Skill Mastery Title")
                    if st.button("CERTIFY"):
                        c.execute("INSERT INTO skill_passport (student_id, skill_name, date_achieved) VALUES (?,?,?)", (sid_s, sk_val, datetime.now().strftime("%Y-%m-%d")))
                        conn.commit(); st.success("Added to Passport!")
            st.subheader("Mastery Registry")
            st.dataframe(pd.read_sql_query("SELECT s.name, sp.skill_name, sp.date_achieved FROM skill_passport sp JOIN students s ON sp.student_id = s.id", conn), use_container_width=True)

        # 🧬 LMS (Point 1)
        with tabs[4]:
            st.header("LMS: Assignments & Homework")
            with st.form("lms"):
                l_g = st.selectbox("Assign to Grade", ["K1-K4", "P1-P6", "S1-S3", "H1-H3"])
                l_t = st.text_input("Task Title")
                l_d = st.date_input("Deadline")
                l_l = st.text_input("Resource Link (Google Drive/Website)")
                if st.form_submit_button("PUBLISH"):
                    c.execute("INSERT INTO assignments (grade, title, deadline, link) VALUES (?,?,?,?)", (l_g, l_t, str(l_d), l_l))
                    conn.commit(); st.success("Homework Published!")
            st.subheader("Homework Board")
            st.dataframe(pd.read_sql_query("SELECT * FROM assignments", conn), use_container_width=True)

        # 🍎 HEALTH/BMI (Point 4)
        with tabs[5]:
            st.header("Health Vital Tracker")
            if not students_df.empty:
                with st.expander("New Vital Record"):
                    sid_h = st.selectbox("Student", students_df['id'], format_func=lambda x: students_df[students_df['id']==x]['name'].values[0], key="h_sid")
                    w = st.number_input("Weight (kg)")
                    h = st.number_input("Height (cm)")
                    if st.button("LOG VITALS"):
                        bmi, stat = calculate_bmi(w, h)
                        c.execute("INSERT INTO health_tracker (student_id, weight, height, bmi, status, date) VALUES (?,?,?,?,?,?)", (sid_h, w, h, bmi, stat, datetime.now().strftime("%Y-%m-%d")))
                        conn.commit(); st.info(f"BMI: {bmi} | Status: {stat}")
            st.subheader("Global Health Log")
            st.dataframe(pd.read_sql_query("SELECT s.name, h.bmi, h.status, h.date FROM health_tracker h JOIN students s ON h.student_id = s.id", conn), use_container_width=True)

        # 🛒 INVENTORY
        with tabs[6]:
            st.header("School Inventory")
            with st.form("inv"):
                itm = st.text_input("Item Name")
                qty = st.number_input("Quantity", min_value=0)
                prc = st.number_input("Unit Price ($)", min_value=0.0)
                if st.form_submit_button("ADD STOCK"):
                    c.execute("INSERT INTO inventory (item_name, stock, price) VALUES (?,?,?)", (itm, qty, prc))
                    conn.commit(); st.success("Updated!")
            st.table(pd.read_sql_query("SELECT * FROM inventory", conn))

        # 🪪 STUDENT CARDS
        with tabs[7]:
            st.header("Student ID Generator")
            if not students_df.empty:
                sel_id = st.selectbox("Select Student", students_df['id'], format_func=lambda x: students_df[students_df['id']==x]['name'].values[0], key="card_sel")
                t_stu = students_df[students_df['id'] == sel_id].iloc[0]
                if st.button("GENERATE CARD"):
                    card_data = generate_student_card(t_stu['name'], t_stu['id'], t_stu['grade'])
                    st.image(card_data)
                    st.download_button("📥 Download PNG", card_data, f"Card_{t_stu['id']}.png", "image/png")

        # 📊 CEO DASHBOARD
        with tabs[8]:
            st.header("Executive Dashboard")
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Students", len(students_df))
            col2.metric("Revenue", f"${(c.execute('SELECT SUM(amount) FROM payments').fetchone()[0] or 0):,.2f}")
            col3.metric("Stock Assets", f"${(c.execute('SELECT SUM(stock * price) FROM inventory').fetchone()[0] or 0):,.2f}")
            if st.button("EXPORT FULL REPORT"):
                df_exp = pd.read_sql_query("SELECT * FROM payments", conn)
                towrap = io.BytesIO(); df_exp.to_excel(towrap, index=False)
                st.download_button("📥 Excel Download", towrap.getvalue(), "JMI_Report.xlsx")

    # --- PARENT VIEW ---
    else:
        sid = st.session_state['student_id']
        s_name = st.session_state['user']
        st.header(f"Parent Portal: {s_name} (ID: {sid})")
        p_tabs = st.tabs(["📜 My Skills", "📅 Attendance", "🧬 Homework", "🍎 Health"])
        
        with p_tabs[0]: st.subheader("Achieved Mastery"); st.table(pd.read_sql_query(f"SELECT skill_name, date_achieved FROM skill_passport WHERE student_id={sid}", conn))
        with p_tabs[1]: st.subheader("Attendance Log"); st.dataframe(pd.read_sql_query(f"SELECT date, status FROM attendance WHERE student_id={sid}", conn), use_container_width=True)
        with p_tabs[2]: 
            st.subheader("Class Assignments")
            c_grade = c.execute("SELECT grade FROM students WHERE id=?", (sid,)).fetchone()[0]
            st.dataframe(pd.read_sql_query(f"SELECT title, deadline, link FROM assignments WHERE grade='{c_grade}'", conn), use_container_width=True)
        with p_tabs[3]: st.subheader("Health/BMI History"); st.dataframe(pd.read_sql_query(f"SELECT weight, height, bmi, status, date FROM health_tracker WHERE student_id={sid}", conn), use_container_width=True)

st.markdown(f"<div class='footer'><b>Prepared by Dr. CHAN Sokhoeurn, C2/DBA</b> | JMI v7.0 | 2026</div>", unsafe_allow_html=True)
