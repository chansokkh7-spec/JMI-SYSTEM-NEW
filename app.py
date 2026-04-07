import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import uuid
import io
import os
from datetime import datetime

# --- 1. DATABASE ENGINE & MULTI-ROLE STRUCTURE ---
DATABASE_NAME = 'jmi_international_v6_7.db'
conn = sqlite3.connect(DATABASE_NAME, check_same_thread=False)
c = conn.cursor()

def init_db():
    # Core Infrastructure
    c.execute('CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, grade TEXT, reg_date TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, amount REAL, date TEXT, staff_name TEXT, transaction_id TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS attendance (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, status TEXT, date TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS skill_passport (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, skill_name TEXT, date_achieved TEXT)')
    # Health & BMI Table (Point 4)
    c.execute('CREATE TABLE IF NOT EXISTS health_tracker (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, weight REAL, height REAL, bmi REAL, status TEXT, date TEXT)')
    # LMS & Assignments Table (Point 1)
    c.execute('CREATE TABLE IF NOT EXISTS assignments (id INTEGER PRIMARY KEY AUTOINCREMENT, grade TEXT, title TEXT, deadline TEXT, link TEXT)')
    # Logistics & Users
    c.execute('CREATE TABLE IF NOT EXISTS curriculum (id INTEGER PRIMARY KEY AUTOINCREMENT, level TEXT, topic TEXT, link TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS inventory (id INTEGER PRIMARY KEY AUTOINCREMENT, item_name TEXT, stock INTEGER, price REAL)')
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)')
    
    # Default Admin: JMI@2026
    admin_hash = hashlib.sha256(str.encode("JMI@2026")).hexdigest()
    c.execute("INSERT OR IGNORE INTO users VALUES (?,?,?)", ('admin', admin_hash, 'Owner'))
    conn.commit()

init_db()

# --- 2. BMI ANALYTICS LOGIC ---
def get_bmi_status(w, h):
    if h > 0:
        bmi = round(w / ((h/100)**2), 2)
        if bmi < 18.5: status = "Underweight"
        elif 18.5 <= bmi <= 24.9: status = "Healthy"
        else: status = "Overweight"
        return bmi, status
    return 0, "N/A"

# --- 3. PREMIUM UI STYLING (Navy & Gold) ---
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

# --- 4. AUTHENTICATION (Point 2: Parental Login) ---
if 'auth' not in st.session_state: st.session_state['auth'] = False

if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_container_width=True)
else:
    st.sidebar.markdown("<h1 style='text-align:center; color:#D4AF37;'>JMI</h1>", unsafe_allow_html=True)

if not st.session_state['auth']:
    st.sidebar.title("SECURE LOGIN")
    u = st.sidebar.text_input("Username")
    p = st.sidebar.text_input("Password", type='password')
    access_mode = st.sidebar.selectbox("Login as", ["CEO/Staff", "Parent/Student"])
    
    if st.sidebar.button("ENTER SYSTEM"):
        if access_mode == "CEO/Staff":
            input_hash = hashlib.sha256(str.encode(p)).hexdigest()
            res = c.execute("SELECT password, role FROM users WHERE username=?", (u,)).fetchone()
            if res and input_hash == res[0]:
                st.session_state.update({"auth": True, "user": u, "role": "Owner"})
                st.rerun()
            else: st.sidebar.error("Invalid Admin Access")
        else:
            # Parental Access Rule: Student Name + Code: JMI2026
            if p == "JMI2026":
                st.session_state.update({"auth": True, "user": u, "role": "Parent"})
                st.rerun()
            else: st.sidebar.error("Parent Access Denied")
else:
    st.sidebar.success(f"Verified: {st.session_state['user']}")
    if st.sidebar.button("LOGOUT"):
        st.session_state['auth'] = False
        st.rerun()

# --- 5. MAIN SYSTEM LOGIC ---
if st.session_state['auth']:
    role = st.session_state['role']
    st.title(f"🏛️ JMI MASTER SYSTEM v6.7")
    
    # Data Pre-load
    students_master = pd.read_sql_query("SELECT id, name, grade FROM students", conn)

    if role == "Owner":
        tabs = st.tabs(["📝 Enrollment", "💰 Payments", "📅 Attendance", "📜 Skill Passport", "🧬 LMS & Homework", "🍎 Health/BMI", "🛒 Inventory", "👤 360 Search", "📊 CEO Dashboard"])
        
        # TAB: ENROLLMENT
        with tabs[0]:
            st.header("Student Registration")
            with st.form("enroll_form"):
                n = st.text_input("Full Name")
                g = st.selectbox("Grade", ["K1-K4", "P1-P6", "S1-S3", "H1-H3", "PUF1-PUF2"])
                if st.form_submit_button("REGISTER"):
                    c.execute("INSERT INTO students (name, grade, reg_date) VALUES (?,?,?)", (n, g, datetime.now().strftime("%Y-%m-%d")))
                    conn.commit(); st.success(f"Enrolled {n}!"); st.rerun()
            st.dataframe(pd.read_sql_query("SELECT * FROM students ORDER BY id DESC", conn), use_container_width=True)

        # TAB: PAYMENTS
        with tabs[1]:
            st.header("Financial Desk")
            if not students_master.empty:
                with st.expander("New Payment"):
                    sid = st.selectbox("Select Student", students_master['id'], format_func=lambda x: students_master[students_master['id']==x]['name'].values[0], key="pay_sid")
                    amt = st.number_input("Amount ($)", min_value=0.0)
                    if st.button("CONFIRM TRANSACTION"):
                        tid = str(uuid.uuid4())[:8].upper()
                        c.execute("INSERT INTO payments (student_id, amount, date, staff_name, transaction_id) VALUES (?,?,?,?,?)", (int(sid), amt, datetime.now().strftime("%Y-%m-%d"), st.session_state['user'], tid))
                        conn.commit(); st.success(f"Receipt Issued: {tid}")
            st.dataframe(pd.read_sql_query("SELECT payments.id, students.name, payments.amount, payments.date FROM payments JOIN students ON payments.student_id = students.id", conn), use_container_width=True)

        # TAB: ATTENDANCE
        with tabs[2]:
            st.header("Teacher Attendance Portal")
            f_grade = st.selectbox("Filter by Class", ["All", "K1-K4", "P1-P6", "S1-S3", "H1-H3", "PUF1-PUF2"])
            att_list = students_master if f_grade == "All" else students_master[students_master['grade'] == f_grade]
            for i, row in att_list.iterrows():
                c1, c2 = st.columns([3, 1])
                c1.write(f"**{row['name']}**")
                status = c2.radio("Mark", ["Present", "Absent"], key=f"att_{row['id']}", horizontal=True)
                if st.button(f"Save {row['id']}", key=f"btn_{row['id']}"):
                    c.execute("INSERT INTO attendance (student_id, status, date) VALUES (?,?,?)", (row['id'], status, datetime.now().strftime("%Y-%m-%d")))
                    conn.commit(); st.toast(f"Saved {row['name']}")

        # TAB: SKILL PASSPORT
        with tabs[3]:
            st.header("Skill Certification")
            if not students_master.empty:
                with st.expander("Issue New Skill"):
                    sid_s = st.selectbox("Student", students_master['id'], format_func=lambda x: students_master[students_master['id']==x]['name'].values[0], key="s_sid")
                    sk_n = st.text_input("Skill Mastery")
                    if st.button("CERTIFY SKILL"):
                        c.execute("INSERT INTO skill_passport (student_id, skill_name, date_achieved) VALUES (?,?,?)", (sid_s, sk_n, datetime.now().strftime("%Y-%m-%d")))
                        conn.commit(); st.success("Certified!")
            st.dataframe(pd.read_sql_query("SELECT students.name, skill_name, date_achieved FROM skill_passport JOIN students ON skill_passport.student_id = students.id", conn), use_container_width=True)

        # TAB: LMS (Point 1)
        with tabs[4]:
            st.header("LMS: Assignment & Homework Manager")
            with st.form("lms_form"):
                target_g = st.selectbox("Assign to Grade", ["K1-K4", "P1-P6", "S1-S3", "H1-H3"])
                title = st.text_input("Assignment Title")
                deadline = st.date_input("Due Date")
                link = st.text_input("Lesson URL")
                if st.form_submit_button("PUBLISH"):
                    c.execute("INSERT INTO assignments (grade, title, deadline, link) VALUES (?,?,?,?)", (target_g, title, str(deadline), link))
                    conn.commit(); st.success("Task Published!")
            st.dataframe(pd.read_sql_query("SELECT * FROM assignments", conn), use_container_width=True)

        # TAB: HEALTH (Point 4)
        with tabs[5]:
            st.header("Medical Growth Analytics (BMI)")
            if not students_master.empty:
                with st.expander("Record Student Vitals"):
                    sid_h = st.selectbox("Student", students_master['id'], format_func=lambda x: students_master[students_master['id']==x]['name'].values[0], key="h_sid")
                    w = st.number_input("Weight (kg)")
                    h = st.number_input("Height (cm)")
                    if st.button("CALCULATE & SAVE"):
                        bmi, status = get_bmi_status(w, h)
                        c.execute("INSERT INTO health_tracker (student_id, weight, height, bmi, status, date) VALUES (?,?,?,?,?,?)", (sid_h, w, h, bmi, status, datetime.now().strftime("%Y-%m-%d")))
                        conn.commit(); st.info(f"BMI: {bmi} ({status})")
            st.dataframe(pd.read_sql_query("SELECT students.name, weight, height, bmi, status, date FROM health_tracker JOIN students ON health_tracker.student_id = students.id", conn), use_container_width=True)

        # TAB: INVENTORY
        with tabs[6]:
            st.header("Inventory Management")
            with st.form("inv"):
                itm = st.text_input("Item Name")
                qty = st.number_input("Qty", min_value=0)
                prc = st.number_input("Price ($)", min_value=0.0)
                if st.form_submit_button("ADD STOCK"):
                    c.execute("INSERT INTO inventory (item_name, stock, price) VALUES (?,?,?)", (itm, qty, prc))
                    conn.commit(); st.success("Stock Updated!")
            st.table(pd.read_sql_query("SELECT * FROM inventory", conn))

        # TAB: 360 SEARCH
        with tabs[7]:
            st.header("Student 360 Insight")
            if not students_master.empty:
                t_id = st.selectbox("Select Profile", students_master['id'], format_func=lambda x: students_master[students_master['id']==x]['name'].values[0])
                c1, c2, c3 = st.columns(3)
                c1.subheader("Skills"); c1.dataframe(pd.read_sql_query(f"SELECT skill_name FROM skill_passport WHERE student_id={t_id}", conn))
                c2.subheader("Finance"); c2.dataframe(pd.read_sql_query(f"SELECT amount, date FROM payments WHERE student_id={t_id}", conn))
                c3.subheader("Health"); c3.dataframe(pd.read_sql_query(f"SELECT bmi, status, date FROM health_tracker WHERE student_id={t_id}", conn))

        # TAB: CEO DASHBOARD
        with tabs[8]:
            st.header("Executive Dashboard")
            m1, m2, m3 = st.columns(3)
            rev = c.execute('SELECT SUM(amount) FROM payments').fetchone()[0] or 0
            m1.metric("Total Revenue", f"${rev:,.2f}")
            m2.metric("Total Students", len(students_master))
            inv_v = c.execute('SELECT SUM(stock * price) FROM inventory').fetchone()[0] or 0
            m3.metric("Inventory Assets", f"${inv_v:,.2f}")
            
            if st.button("EXPORT SYSTEM DATA"):
                df_exp = pd.read_sql_query("SELECT * FROM payments", conn)
                towrap = io.BytesIO(); df_exp.to_excel(towrap, index=False)
                st.download_button("📥 Download Excel", towrap.getvalue(), "JMI_Report.xlsx")

    # --- PARENTAL PORTAL VIEW ---
    else:
        parent_child = st.session_state['user']
        child_profile = students_master[students_master['name'] == parent_child]
        
        if child_profile.empty:
            st.warning("Profile not found. Please contact administration.")
        else:
            cid = int(child_profile['id'].values[0])
            c_grade = child_profile['grade'].values[0]
            p_tabs = st.tabs(["👤 My Child", "📜 Skills", "📅 Attendance", "🧬 Homework", "🍎 Health"])
            
            with p_tabs[0]: st.header(f"Profile: {parent_child}"); st.write(f"**Grade:** {c_grade}")
            with p_tabs[1]: st.subheader("Achieved Skills"); st.table(pd.read_sql_query(f"SELECT skill_name, date_achieved FROM skill_passport WHERE student_id={cid}", conn))
            with p_tabs[2]: st.subheader("Attendance Log"); st.dataframe(pd.read_sql_query(f"SELECT date, status FROM attendance WHERE student_id={cid}", conn))
            with p_tabs[3]: st.subheader("Homework & Assignments"); st.dataframe(pd.read_sql_query(f"SELECT title, deadline, link FROM assignments WHERE grade='{c_grade}'", conn))
            with p_tabs[4]: st.subheader("Health Report (BMI)"); st.dataframe(pd.read_sql_query(f"SELECT weight, height, bmi, status, date FROM health_tracker WHERE student_id={cid}", conn))

# --- FOOTER ---
st.markdown(f"<div class='footer'><b>Prepared by Dr. CHAN Sokhoeurn, C2/DBA</b> | JMI v6.7 | 2026</div>", unsafe_allow_html=True)
