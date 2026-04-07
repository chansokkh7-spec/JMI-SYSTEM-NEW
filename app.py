import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import uuid
import io
from datetime import datetime

# --- 1. DATABASE INITIALIZATION ---
conn = sqlite3.connect('jmi_v6_enterprise.db', check_same_thread=False)
c = conn.cursor()

def init_db():
    # Tables ចាស់ៗ
    c.execute('CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, grade TEXT, reg_date TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, amount REAL, date TEXT, staff_name TEXT, transaction_id TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS attendance (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, status TEXT, date TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)')
    
    # Tables ថ្មីៗសម្រាប់ v6.0
    c.execute('CREATE TABLE IF NOT EXISTS skill_passport (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, skill_name TEXT, date_achieved TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS health_tracker (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, weight REAL, height REAL, diet_note TEXT, date TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS inventory (id INTEGER PRIMARY KEY AUTOINCREMENT, item_name TEXT, stock INTEGER, price REAL)')
    c.execute('CREATE TABLE IF NOT EXISTS curriculum (id INTEGER PRIMARY KEY AUTOINCREMENT, level TEXT, topic TEXT, link TEXT)')
    
    admin_hash = hashlib.sha256(str.encode("JMI@2026")).hexdigest()
    c.execute("INSERT OR IGNORE INTO users VALUES (?,?,?)", ('admin', admin_hash, 'Owner'))
    conn.commit()

init_db()

# --- 2. THEME & STYLE ---
st.set_page_config(page_title="JMI Master Portal", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #000033; }
    [data-testid="stSidebar"] { background-color: #00001a !important; border-right: 2px solid #D4AF37; }
    h1, h2, h3, label, p, span, .stMarkdown { color: #D4AF37 !important; }
    .stButton>button { background-color: #D4AF37; color: #000033; border-radius: 8px; font-weight: bold; border: 1px solid #FFD700; width: 100%; }
    .stTabs [data-baseweb="tab"] { color: #D4AF37 !important; font-size: 14px; }
    .footer { position: fixed; bottom: 0; left: 0; width: 100%; background-color: #00001a; text-align: center; padding: 5px; color: #D4AF37; border-top: 1px solid #D4AF37; z-index: 100; }
    input, select, textarea { background-color: #000055 !important; color: white !important; border: 1px solid #D4AF37 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. AUTHENTICATION ---
if 'auth' not in st.session_state: st.session_state['auth'] = False

if not st.session_state['auth']:
    st.sidebar.markdown("<h2 style='text-align:center;'>JMI LOGIN</h2>", unsafe_allow_html=True)
    u = st.sidebar.text_input("Username")
    p = st.sidebar.text_input("Password", type='password')
    if st.sidebar.button("LOGIN"):
        input_hash = hashlib.sha256(str.encode(p)).hexdigest()
        res = c.execute("SELECT password, role FROM users WHERE username=?", (u,)).fetchone()
        if res and input_hash == res[0]:
            st.session_state.update({"auth": True, "user": u, "role": res[1]})
            st.rerun()
        else: st.sidebar.error("Invalid Credentials")
else:
    st.sidebar.markdown(f"👤 **{st.session_state['user']}** ({st.session_state['role']})")
    if st.sidebar.button("LOGOUT"):
        st.session_state['auth'] = False
        st.rerun()

# --- 4. MAIN SYSTEM ---
if st.session_state['auth']:
    role = st.session_state['role']
    st.title(f"🏛️ JMI MASTER SYSTEM v6.0")

    # ការបែងចែក Tabs តាមតួនាទី
    menu = ["📝 Enrollment", "💰 Payments", "📅 Attendance", "📜 Skill Passport", "🧬 Curriculum", "🍎 Health", "🛒 Inventory"]
    if role == "Owner": menu.append("📊 CEO Dashboard")
    
    tabs = st.tabs(menu)

    # --- TAB: ENROLLMENT ---
    with tabs[0]:
        st.header("Student Registration")
        with st.form("reg"):
            name = st.text_input("Full Name")
            grade = st.selectbox("Grade", ["K1-K4", "P1-P6", "S1-S3", "H1-H3", "PUF1-PUF2"])
            if st.form_submit_button("SUBMIT"):
                c.execute("INSERT INTO students (name, grade, reg_date) VALUES (?,?,?)", (name, grade, datetime.now().strftime("%Y-%m-%d")))
                conn.commit()
                st.success(f"{name} Registered!")

    # --- TAB: PAYMENTS ---
    with tabs[1]:
        st.header("Financial Collection")
        sts = pd.read_sql_query("SELECT id, name FROM students", conn)
        if not sts.empty:
            sid = st.selectbox("Select Student", sts['id'], format_func=lambda x: sts[sts['id']==x]['name'].values[0], key="pay_sid")
            amt = st.number_input("Amount ($)", min_value=0.0)
            if st.button("COLLECT"):
                tid = str(uuid.uuid4())[:8].upper()
                c.execute("INSERT INTO payments (student_id, amount, date, staff_name, transaction_id) VALUES (?,?,?,?,?)", (int(sid), amt, datetime.now().strftime("%Y-%m-%d"), st.session_state['user'], tid))
                conn.commit()
                st.info(f"Receipt ID: {tid} | Telegram notification sent (Simulated)")

    # --- TAB: ATTENDANCE ---
    with tabs[2]:
        st.header("Daily Attendance")
        st_data = pd.read_sql_query("SELECT id, name FROM students", conn)
        for i, row in st_data.iterrows():
            col1, col2 = st.columns([3, 1])
            col1.write(f"**{row['name']}**")
            status = col2.radio("Status", ["Present", "Absent"], key=f"att_{row['id']}")
            if st.button(f"Save for {row['name']}", key=f"btn_{row['id']}"):
                c.execute("INSERT INTO attendance (student_id, status, date) VALUES (?,?,?)", (row['id'], status, datetime.now().strftime("%Y-%m-%d")))
                conn.commit()
                st.toast("Saved!")

    # --- TAB 1: SKILL PASSPORT ---
    with tabs[3]:
        st.header("📜 Skill Passport & Certification")
        if not sts.empty:
            sid_skill = st.selectbox("Select Student", sts['id'], format_func=lambda x: sts[sts['id']==x]['name'].values[0], key="skill_sid")
            skill = st.text_input("New Skill Mastered (e.g., First Aid, Anatomy Basics)")
            if st.button("Add Skill to Passport"):
                c.execute("INSERT INTO skill_passport (student_id, skill_name, date_achieved) VALUES (?,?,?)", (sid_skill, skill, datetime.now().strftime("%Y-%m-%d")))
                conn.commit()
                st.success("Skill Recorded!")
            
            st.subheader("Student Skill History")
            df_skills = pd.read_sql_query(f"SELECT skill_name, date_achieved FROM skill_passport WHERE student_id={sid_skill}", conn)
            st.table(df_skills)

    # --- TAB 2: CURRICULUM ---
    with tabs[4]:
        st.header("🧬 Medical Curriculum Library")
        if role == "Owner":
            with st.expander("Add New Lesson Material"):
                l_grade = st.selectbox("For Grade", ["K1-K4", "P1-P6", "S1-S3", "H1-H3", "PUF1-PUF2"], key="curr_grade")
                l_topic = st.text_input("Topic Name")
                l_link = st.text_input("Resource Link (Drive/PDF)")
                if st.button("Upload Material"):
                    c.execute("INSERT INTO curriculum (level, topic, link) VALUES (?,?,?)", (l_grade, l_topic, l_link))
                    conn.commit()
        
        target_grade = st.selectbox("Filter by Grade", ["K1-K4", "P1-P6", "S1-S3", "H1-H3", "PUF1-PUF2"])
        df_curr = pd.read_sql_query(f"SELECT topic, link FROM curriculum WHERE level='{target_grade}'", conn)
        st.dataframe(df_curr, use_container_width=True)

    # --- TAB 3: HEALTH TRACKER ---
    with tabs[5]:
        st.header("🍎 Nutrition & Health Tracker")
        if not sts.empty:
            sid_health = st.selectbox("Select Student", sts['id'], format_func=lambda x: sts[sts['id']==x]['name'].values[0], key="h_sid")
            colh1, colh2 = st.columns(2)
            w = colh1.number_input("Weight (kg)", min_value=0.0)
            h = colh2.number_input("Height (cm)", min_value=0.0)
            diet = st.text_area("Dietary/Health Notes")
            if st.button("Log Health Data"):
                c.execute("INSERT INTO health_tracker (student_id, weight, height, diet_note, date) VALUES (?,?,?,?,?)", (sid_health, w, h, diet, datetime.now().strftime("%Y-%m-%d")))
                conn.commit()
                st.success("Health data logged!")

    # --- TAB 4: INVENTORY ---
    with tabs[6]:
        st.header("🛒 Merchandising & Inventory")
        if role == "Owner":
            with st.expander("Add/Update Stock"):
                i_name = st.text_input("Item Name (e.g., Doctor Coat)")
                i_qty = st.number_input("Quantity", min_value=0)
                i_prc = st.number_input("Price ($)", min_value=0.0)
                if st.button("Update Inventory"):
                    c.execute("INSERT INTO inventory (item_name, stock, price) VALUES (?,?,?)", (i_name, i_qty, i_prc))
                    conn.commit()
        
        df_inv = pd.read_sql_query("SELECT * FROM inventory", conn)
        st.table(df_inv)

    # --- TAB 5: CEO DASHBOARD ---
    if role == "Owner":
        with tabs[7]:
            st.header("📊 CEO Executive Dashboard")
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Revenue", f"${c.execute('SELECT SUM(amount) FROM payments').fetchone()[0] or 0:,.2f}")
            col2.metric("Active Students", c.execute('SELECT COUNT(*) FROM students').fetchone()[0])
            col3.metric("Inventory Value", f"${c.execute('SELECT SUM(stock * price) FROM inventory').fetchone()[0] or 0:,.2f}")

st.markdown(f"<div class='footer'><b>Prepared by CHAN Sokhoeurn, C2/DBA</b> | JMI v6.0 Blue Ocean System</div>", unsafe_allow_html=True)
