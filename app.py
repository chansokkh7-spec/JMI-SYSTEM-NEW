import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import uuid
import io
from datetime import datetime
import os

# --- 1. DATABASE SETUP ---
DATABASE_NAME = 'jmi_enterprise_v6_5.db'
conn = sqlite3.connect(DATABASE_NAME, check_same_thread=False)
c = conn.cursor()

def init_db():
    c.execute('CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, grade TEXT, reg_date TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, amount REAL, date TEXT, staff_name TEXT, transaction_id TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS attendance (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, status TEXT, date TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS skill_passport (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, skill_name TEXT, date_achieved TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS health_tracker (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, weight REAL, height REAL, diet_note TEXT, date TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS curriculum (id INTEGER PRIMARY KEY AUTOINCREMENT, level TEXT, topic TEXT, link TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS inventory (id INTEGER PRIMARY KEY AUTOINCREMENT, item_name TEXT, stock INTEGER, price REAL)')
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)')
    admin_hash = hashlib.sha256(str.encode("JMI@2026")).hexdigest()
    c.execute("INSERT OR IGNORE INTO users VALUES (?,?,?)", ('admin', admin_hash, 'Owner'))
    conn.commit()

init_db()

# --- 2. PREMIUM UI STYLING ---
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
    div[data-testid="stMetricValue"] { color: #D4AF37 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. LOGO INTEGRATION ---
# REPLACE "logo.png" WITH YOUR ACTUAL FILENAME
LOGO_PATH = "logo.png" 

def display_logo(location="sidebar"):
    if os.path.exists(LOGO_PATH):
        if location == "sidebar":
            st.sidebar.image(LOGO_PATH, use_container_width=True)
        else:
            st.image(LOGO_PATH, width=150)
    else:
        if location == "sidebar":
            st.sidebar.markdown("<h1 style='text-align: center; color: #D4AF37;'>JMI</h1>", unsafe_allow_html=True)

# --- 4. AUTHENTICATION ---
if 'auth' not in st.session_state: st.session_state['auth'] = False

display_logo(location="sidebar") # Show logo in sidebar

if not st.session_state['auth']:
    st.sidebar.title("JMI LOGIN")
    u = st.sidebar.text_input("Username")
    p = st.sidebar.text_input("Password", type='password')
    if st.sidebar.button("LOG IN"):
        input_hash = hashlib.sha256(str.encode(p)).hexdigest()
        res = c.execute("SELECT password, role FROM users WHERE username=?", (u,)).fetchone()
        if res and input_hash == res[0]:
            st.session_state.update({"auth": True, "user": u, "role": res[1]})
            st.rerun()
        else: st.sidebar.error("Invalid Credentials")
else:
    st.sidebar.success(f"Welcome, {st.session_state['user']}")
    if st.sidebar.button("LOG OUT"):
        st.session_state['auth'] = False
        st.rerun()

# --- 5. MAIN SYSTEM ---
if st.session_state['auth']:
    role = st.session_state['role']
    
    # Header with Logo and Title
    col_l, col_t = st.columns([1, 5])
    with col_l:
        display_logo(location="header")
    with col_t:
        st.title("JMI MASTER SYSTEM v6.5")
    
    tabs = st.tabs(["📝 Enrollment", "💰 Payments", "📅 Attendance", "📜 Skill Passport", "🧬 Curriculum", "🍎 Health", "🛒 Inventory", "👤 Student Search", "📊 CEO Dashboard"])

    # Global Data Loading
    students_master = pd.read_sql_query("SELECT id, name, grade FROM students", conn)

    # --- TAB 1: ENROLLMENT ---
    with tabs[0]:
        st.header("Enrollment Portal")
        with st.form("enroll"):
            n = st.text_input("Student Name")
            g = st.selectbox("Grade Level", ["K1-K4", "P1-P6", "S1-S3", "H1-H3", "PUF1-PUF2"])
            if st.form_submit_button("SUBMIT"):
                if n:
                    c.execute("INSERT INTO students (name, grade, reg_date) VALUES (?,?,?)", (n, g, datetime.now().strftime("%Y-%m-%d")))
                    conn.commit()
                    st.success(f"Successfully Enrolled {n}!")
                    st.rerun()
        st.subheader("Global Student List")
        st.dataframe(pd.read_sql_query("SELECT * FROM students ORDER BY id DESC", conn), use_container_width=True)

    # --- TAB 2: PAYMENTS ---
    with tabs[1]:
        st.header("Financial Collection")
        if not students_master.empty:
            with st.expander("Record New Tuition Payment"):
                sid = st.selectbox("Select Student", students_master['id'], format_func=lambda x: students_master[students_master['id']==x]['name'].values[0])
                amt = st.number_input("Amount ($)", min_value=0.0)
                if st.button("CONFIRM PAYMENT"):
                    tid = str(uuid.uuid4())[:8].upper()
                    c.execute("INSERT INTO payments (student_id, amount, date, staff_name, transaction_id) VALUES (?,?,?,?,?)", (int(sid), amt, datetime.now().strftime("%Y-%m-%d"), st.session_state['user'], tid))
                    conn.commit()
                    st.success(f"Payment Confirmed! Receipt: {tid}")
        st.subheader("Transaction History")
        st.dataframe(pd.read_sql_query("SELECT payments.id, students.name, payments.amount, payments.date, payments.transaction_id FROM payments JOIN students ON payments.student_id = students.id", conn), use_container_width=True)

    # --- TAB 3: ATTENDANCE ---
    with tabs[2]:
        st.header("Daily Attendance")
        grade_f = st.selectbox("Filter Class", ["All", "K1-K4", "P1-P6", "S1-S3", "H1-H3", "PUF1-PUF2"])
        display_list = students_master if grade_f == "All" else students_master[students_master['grade'] == grade_f]
        if not display_list.empty:
            for i, row in display_list.iterrows():
                col1, col2 = st.columns([3, 1])
                col1.write(f"**{row['name']}**")
                status = col2.radio("Status", ["Present", "Absent"], key=f"att_{row['id']}", horizontal=True)
                if st.button(f"Save: {row['name']}", key=f"btn_{row['id']}"):
                    c.execute("INSERT INTO attendance (student_id, status, date) VALUES (?,?,?)", (row['id'], status, datetime.now().strftime("%Y-%m-%d")))
                    conn.commit()
                    st.toast(f"Recorded: {row['name']}")
        else: st.info("No students found.")

    # --- TAB 4: SKILL PASSPORT ---
    with tabs[3]:
        st.header("📜 Skill Certification")
        if not students_master.empty:
            with st.expander("Certify Mastery"):
                sid_s = st.selectbox("Student", students_master['id'], format_func=lambda x: students_master[students_master['id']==x]['name'].values[0], key="sk_sid")
                sk_name = st.text_input("Skill Topic")
                if st.button("ISSUE"):
                    c.execute("INSERT INTO skill_passport (student_id, skill_name, date_achieved) VALUES (?,?,?)", (sid_s, sk_name, datetime.now().strftime("%Y-%m-%d")))
                    conn.commit()
                    st.success("Skill Added!")
        st.dataframe(pd.read_sql_query("SELECT students.name, skill_passport.skill_name, skill_passport.date_achieved FROM skill_passport JOIN students ON skill_passport.student_id = students.id", conn), use_container_width=True)

    # --- TAB 5: CURRICULUM ---
    with tabs[4]:
        st.header("🧬 Medical Curriculum")
        if role == "Owner":
            with st.expander("Upload Material"):
                l_v = st.selectbox("Level", ["K1-K4", "P1-P6", "S1-S3", "H1-H3"])
                l_t = st.text_input("Topic")
                l_l = st.text_input("Link")
                if st.button("SAVE"):
                    c.execute("INSERT INTO curriculum (level, topic, link) VALUES (?,?,?)", (l_v, l_t, l_l))
                    conn.commit()
        st.dataframe(pd.read_sql_query("SELECT * FROM curriculum", conn), use_container_width=True)

    # --- TAB 6: HEALTH ---
    with tabs[5]:
        st.header("🍎 Health Tracker")
        if not students_master.empty:
            with st.expander("Log Vitals"):
                sid_h = st.selectbox("Student", students_master['id'], format_func=lambda x: students_master[students_master['id']==x]['name'].values[0], key="h_sid")
                h_c1, h_c2 = st.columns(2)
                w = h_c1.number_input("Weight (kg)", min_value=0.0)
                h = h_c2.number_input("Height (cm)", min_value=0.0)
                if st.button("LOG"):
                    c.execute("INSERT INTO health_tracker (student_id, weight, height, date) VALUES (?,?,?,?)", (sid_h, w, h, datetime.now().strftime("%Y-%m-%d")))
                    conn.commit()
                    st.success("Logged!")
        st.dataframe(pd.read_sql_query("SELECT students.name, weight, height, date FROM health_tracker JOIN students ON health_tracker.student_id = students.id", conn), use_container_width=True)

    # --- TAB 7: INVENTORY ---
    with tabs[6]:
        st.header("🛒 Inventory")
        if role == "Owner":
            with st.expander("Stock Update"):
                itm = st.text_input("Item")
                qty = st.number_input("Qty", min_value=0)
                prc = st.number_input("Price ($)", min_value=0.0)
                if st.button("ADD"):
                    c.execute("INSERT INTO inventory (item_name, stock, price) VALUES (?,?,?)", (itm, qty, prc))
                    conn.commit()
        st.table(pd.read_sql_query("SELECT * FROM inventory", conn))

    # --- TAB 8: STUDENT SEARCH ---
    with tabs[7]:
        st.header("👤 360° Search")
        if not students_master.empty:
            target = st.selectbox("Select Profile", students_master['id'], format_func=lambda x: students_master[students_master['id']==x]['name'].values[0])
            c1, c2, c3 = st.columns(3)
            c1.write("**Skills**")
            c1.dataframe(pd.read_sql_query(f"SELECT skill_name FROM skill_passport WHERE student_id={target}", conn))
            c2.write("**Tuition**")
            c2.dataframe(pd.read_sql_query(f"SELECT amount, date FROM payments WHERE student_id={target}", conn))
            c3.write("**Health**")
            c3.dataframe(pd.read_sql_query(f"SELECT weight, height, date FROM health_tracker WHERE student_id={target}", conn))

    # --- TAB 9: CEO DASHBOARD ---
    with tabs[8]:
        st.header("📊 CEO Dashboard")
        m1, m2, m3 = st.columns(3)
        rev = c.execute('SELECT SUM(amount) FROM payments').fetchone()[0] or 0
        m1.metric("Total Revenue", f"${rev:,.2f}")
        m2.metric("Total Students", len(students_master))
        inv_v = c.execute('SELECT SUM(stock * price) FROM inventory').fetchone()[0] or 0
        m3.metric("Inventory Value", f"${inv_v:,.2f}")
        
        if st.button("EXPORT DATA"):
            df_export = pd.read_sql_query("SELECT * FROM payments", conn)
            towrap = io.BytesIO()
            df_export.to_excel(towrap, index=False)
            st.download_button("📥 Download Excel", towrap.getvalue(), "JMI_Report.xlsx")

# --- FOOTER ---
st.markdown(f"<div class='footer'><b>Prepared by Dr. CHAN Sokhoeurn, C2/DBA</b> | JMI v6.5 | 2026</div>", unsafe_allow_html=True)
