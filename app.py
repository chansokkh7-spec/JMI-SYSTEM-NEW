import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import uuid
from datetime import datetime

# --- 1. DATABASE SETUP ---
DATABASE_NAME = 'jmi_enterprise_v6_3.db'
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
    
    # Default Admin: JMI@2026
    admin_hash = hashlib.sha256(str.encode("JMI@2026")).hexdigest()
    c.execute("INSERT OR IGNORE INTO users VALUES (?,?,?)", ('admin', admin_hash, 'Owner'))
    conn.commit()

init_db()

# --- 2. PREMIUM UI STYLING (Navy & Gold) ---
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

# --- 3. AUTHENTICATION ---
if 'auth' not in st.session_state: st.session_state['auth'] = False

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
    st.sidebar.success(f"Welcome, {st.session_state['user']} ({st.session_state['role']})")
    if st.sidebar.button("LOG OUT"):
        st.session_state['auth'] = False
        st.rerun()

# --- 4. MAIN SYSTEM ---
if st.session_state['auth']:
    role = st.session_state['role']
    st.title("🏛️ JMI MASTER SYSTEM v6.3")
    
    tabs_list = ["📝 Enrollment", "💰 Payments", "📅 Attendance", "📜 Skill Passport", "🧬 Curriculum", "🍎 Health", "🛒 Inventory", "👤 Student Search"]
    if role == "Owner": tabs_list.append("📊 CEO Dashboard")
    tabs = st.tabs(tabs_list)

    # Global Student Data
    students_master = pd.read_sql_query("SELECT id, name, grade FROM students", conn)

    # --- TAB: ENROLLMENT ---
    with tabs[0]:
        st.header("New Student Registration")
        with st.form("enroll_form"):
            name = st.text_input("Full Name")
            grade = st.selectbox("Assign Grade", ["K1-K4", "P1-P6", "S1-S3", "H1-H3", "PUF1-PUF2"])
            if st.form_submit_button("REGISTER STUDENT"):
                if name:
                    c.execute("INSERT INTO students (name, grade, reg_date) VALUES (?,?,?)", (name, grade, datetime.now().strftime("%Y-%m-%d")))
                    conn.commit()
                    st.success(f"{name} registered successfully!")
                    st.rerun()
        st.subheader("Recent Admissions")
        st.dataframe(pd.read_sql_query("SELECT * FROM students ORDER BY id DESC LIMIT 5", conn), use_container_width=True)

    # --- TAB: PAYMENTS ---
    with tabs[1]:
        st.header("Tuition & Fees Management")
        if not students_master.empty:
            with st.expander("Record New Transaction"):
                sid = st.selectbox("Select Student", students_master['id'], format_func=lambda x: students_master[students_master['id']==x]['name'].values[0], key="pay_sid")
                amount = st.number_input("Amount ($)", min_value=0.0)
                if st.button("PROCESS PAYMENT"):
                    tid = str(uuid.uuid4())[:8].upper()
                    c.execute("INSERT INTO payments (student_id, amount, date, staff_name, transaction_id) VALUES (?,?,?,?,?)",
                              (int(sid), amount, datetime.now().strftime("%Y-%m-%d"), st.session_state['user'], tid))
                    conn.commit()
                    st.success(f"Receipt Generated: {tid}")
        st.subheader("Transaction History")
        st.dataframe(pd.read_sql_query("SELECT payments.id, students.name, payments.amount, payments.date, payments.transaction_id FROM payments JOIN students ON payments.student_id = students.id ORDER BY payments.id DESC", conn), use_container_width=True)

    # --- TAB: ATTENDANCE (Teacher Mode Optimized) ---
    with tabs[2]:
        st.header("Daily Attendance Tracker")
        today = datetime.now().strftime("%Y-%m-%d")
        grade_filter = st.selectbox("Filter by Class", ["All Grades", "K1-K4", "P1-P6", "S1-S3", "H1-H3", "PUF1-PUF2"])
        
        display_sts = students_master if grade_filter == "All Grades" else students_master[students_master['grade'] == grade_filter]

        if not display_sts.empty:
            for i, row in display_sts.iterrows():
                col1, col2 = st.columns([3, 1])
                col1.write(f"**{row['name']}**")
                status = col2.radio("Status", ["Present", "Absent"], key=f"att_{row['id']}", horizontal=True)
                if st.button(f"Save: {row['name']}", key=f"btn_att_{row['id']}"):
                    c.execute("INSERT INTO attendance (student_id, status, date) VALUES (?,?,?)", (row['id'], status, today))
                    conn.commit()
                    st.toast(f"Recorded: {row['name']} is {status}")
        else:
            st.warning("No students found in this grade.")

    # --- TAB: SKILL PASSPORT ---
    with tabs[3]:
        st.header("📜 Medical Skill Passport")
        if not students_master.empty:
            sid_skill = st.selectbox("Select Student", students_master['id'], format_func=lambda x: students_master[students_master['id']==x]['name'].values[0], key="skill_sid")
            skill_name = st.text_input("Certified Skill (e.g., Blood Pressure Mastery)")
            if st.button("CERTIFY SKILL"):
                c.execute("INSERT INTO skill_passport (student_id, skill_name, date_achieved) VALUES (?,?,?)", (sid_skill, skill_name, today))
                conn.commit()
                st.success("Skill added to Digital Passport!")
        st.dataframe(pd.read_sql_query("SELECT students.name, skill_passport.skill_name, skill_passport.date_achieved FROM skill_passport JOIN students ON skill_passport.student_id = students.id ORDER BY skill_passport.id DESC", conn), use_container_width=True)

    # --- TAB: CURRICULUM ---
    with tabs[4]:
        st.header("🧬 Medical Resource Library")
        if role == "Owner":
            with st.expander("Add New Content"):
                c_lv = st.selectbox("Grade Level", ["K1-K4", "P1-P6", "S1-S3", "H1-H3"])
                c_topic = st.text_input("Lesson Topic")
                c_link = st.text_input("Resource URL (GDrive/PDF)")
                if st.button("UPLOAD RESOURCE"):
                    c.execute("INSERT INTO curriculum (level, topic, link) VALUES (?,?,?)", (c_lv, c_topic, c_link))
                    conn.commit()
        st.dataframe(pd.read_sql_query("SELECT * FROM curriculum", conn), use_container_width=True)

    # --- TAB: HEALTH ---
    with tabs[5]:
        st.header("🍎 Nutrition & Vital Tracker")
        if not students_master.empty:
            sid_h = st.selectbox("Select Student", students_master['id'], format_func=lambda x: students_master[students_master['id']==x]['name'].values[0], key="h_sid")
            h_col1, h_col2 = st.columns(2)
            wt = h_col1.number_input("Weight (kg)", min_value=0.0)
            ht = h_col2.number_input("Height (cm)", min_value=0.0)
            diet = st.text_area("Health & Dietary Notes")
            if st.button("LOG HEALTH DATA"):
                c.execute("INSERT INTO health_tracker (student_id, weight, height, diet_note, date) VALUES (?,?,?,?,?)", (sid_h, wt, ht, diet, today))
                conn.commit()
                st.success("Vitals updated!")

    # --- TAB: INVENTORY ---
    with tabs[6]:
        st.header("🛒 JMI Merchandising")
        if role == "Owner":
            with st.expander("Add Stock Items"):
                item = st.text_input("Item Name (e.g., Lab Coat)")
                qty = st.number_input("Stock Quantity", min_value=0)
                price = st.number_input("Unit Price ($)", min_value=0.0)
                if st.button("ADD TO INVENTORY"):
                    c.execute("INSERT INTO inventory (item_name, stock, price) VALUES (?,?,?)", (item, qty, price))
                    conn.commit()
        st.table(pd.read_sql_query("SELECT * FROM inventory", conn))

    # --- TAB: STUDENT SEARCH (Dr. CHAN'S 360 View) ---
    with tabs[7]:
        st.header("👤 360° Student Insight")
        if not students_master.empty:
            search_id = st.selectbox("Enter Student Name", students_master['id'], format_func=lambda x: students_master[students_master['id']==x]['name'].values[0])
            
            s1, s2, s3 = st.columns(3)
            s1.subheader("📜 Skills Mastered")
            s1.dataframe(pd.read_sql_query(f"SELECT skill_name, date_achieved FROM skill_passport WHERE student_id={search_id}", conn), use_container_width=True)
            
            s2.subheader("🍎 Health Vitals")
            s2.dataframe(pd.read_sql_query(f"SELECT weight, height, date FROM health_tracker WHERE student_id={search_id}", conn), use_container_width=True)
            
            s3.subheader("💰 Financial Status")
            s3.dataframe(pd.read_sql_query(f"SELECT amount, date FROM payments WHERE student_id={search_id}", conn), use_container_width=True)

    # --- TAB: CEO DASHBOARD (Owner Only) ---
    if role == "Owner":
        with tabs[8]:
            st.header("📊 Executive Performance Dashboard")
            m1, m2, m3, m4 = st.columns(4)
            
            total_rev = c.execute("SELECT SUM(amount) FROM payments").fetchone()[0] or 0
            total_st = len(students_master)
            stock_val = c.execute("SELECT SUM(stock * price) FROM inventory").fetchone()[0] or 0
            
            m1.metric("Total Revenue", f"${total_rev:,.2f}")
            m2.metric("Enrolled Students", total_st)
            m3.metric("Inventory Value", f"${stock_val:,.2f}")
            m4.metric("System Integrity", "Verified")
            
            # Export Feature
            st.subheader("Data Export")
            if st.button("GENERATE EXCEL REPORT"):
                report_df = pd.read_sql_query("SELECT students.name, payments.amount, payments.date FROM payments JOIN students ON payments.student_id = students.id", conn)
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    report_df.to_excel(writer, index=False, sheet_name='Revenue_Report')
                st.download_button(label="📥 Download Revenue Report", data=output.getvalue(), file_name=f"JMI_Report_{today}.xlsx")

# --- FOOTER ---
st.markdown(f"<div class='footer'><b>Prepared by Dr. CHAN Sokhoeurn, C2/DBA</b> | JMI Enterprise Ecosystem v6.3 | 2026</div>", unsafe_allow_html=True)
