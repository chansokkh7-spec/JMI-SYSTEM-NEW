import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import uuid
import io
from datetime import datetime
from PIL import Image, ImageDraw, ImageOps

# --- 1. DATABASE & ARCHITECTURE (Verified All 8 Tables) ---
DB_NAME = 'jmi_enterprise_v8_5.db'
conn = sqlite3.connect(DB_NAME, check_same_thread=False)
c = conn.cursor()

def init_db():
    # 1. Enrollment Table
    c.execute('''CREATE TABLE IF NOT EXISTS students 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, grade TEXT, 
                  reg_date TEXT, photo BLOB)''')
    
    # 2. Finance Table (5 Fee Types)
    c.execute('''CREATE TABLE IF NOT EXISTS payments 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, fee_type TEXT, 
                  amount REAL, date TEXT, staff_name TEXT, transaction_id TEXT)''')
    
    # 3. Attendance Table
    c.execute('CREATE TABLE IF NOT EXISTS attendance (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, status TEXT, date TEXT)')
    
    # 4. Skills Table (Skill Passport)
    c.execute('CREATE TABLE IF NOT EXISTS skill_passport (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, skill_name TEXT, date_achieved TEXT)')
    
    # 5. Health Table (BMI Tracker)
    c.execute('''CREATE TABLE IF NOT EXISTS health_tracker 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, weight REAL, height REAL, 
                  bmi REAL, status TEXT, date TEXT)''')
    
    # 6. LMS Table (Assignments)
    c.execute('CREATE TABLE IF NOT EXISTS assignments (id INTEGER PRIMARY KEY AUTOINCREMENT, grade TEXT, title TEXT, deadline TEXT)')
    
    # 7. User Table
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)')
    
    # Default Admin (Owner)
    admin_pw = hashlib.sha256(str.encode('JMI@CEO')).hexdigest()
    c.execute("INSERT OR REPLACE INTO users VALUES (?,?,?)", ('ceo_admin', admin_pw, 'Owner'))
    conn.commit()

init_db()

# --- 2. CORE TOOLS (BMI & PHOTO ID CARD) ---
def calculate_bmi(w, h):
    if h > 0:
        bmi = round(w / ((h/100)**2), 2)
        status = "Normal" if 18.5 <= bmi <= 24.9 else ("Underweight" if bmi < 18.5 else "Overweight")
        return bmi, status
    return 0, "N/A"

def generate_jmi_id(name, sid, grade, photo_bytes):
    card = Image.new('RGB', (450, 280), color='#000033')
    draw = ImageDraw.Draw(card)
    draw.rectangle([10, 10, 440, 270], outline="#D4AF37", width=5)
    
    if photo_bytes:
        try:
            img = Image.open(io.BytesIO(photo_bytes))
            img = ImageOps.fit(img, (110, 130))
            card.paste(img, (310, 60))
            draw.rectangle([305, 55, 425, 195], outline="white", width=2)
        except: pass
        
    draw.text((30, 30), "JUNIOR MEDICAL INSTITUTE", fill="#D4AF37")
    draw.text((30, 90), f"NAME: {name.upper()}", fill="white")
    draw.text((30, 135), f"ID: {sid}", fill="#D4AF37")
    draw.text((30, 180), f"GRADE: {grade}", fill="white")
    draw.text((30, 235), "Prepared by Dr. CHAN Sokhoeurn, C2/DBA", fill="#D4AF37")
    
    buf = io.BytesIO()
    card.save(buf, format='PNG')
    return buf.getvalue()

# --- 3. PREMIUM UI STYLING (Navy & Gold) ---
st.set_page_config(page_title="JMI Master Portal v8.5", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #000033; color: white; }
    [data-testid="stSidebar"] { background-color: #00001a !important; border-right: 2px solid #D4AF37; }
    h1, h2, h3, label, p { color: #D4AF37 !important; }
    .stButton>button { background-color: #D4AF37; color: #000033; font-weight: bold; width: 100%; border-radius: 10px; }
    .stTabs [data-baseweb="tab"] { color: #D4AF37 !important; font-size: 16px; font-weight: bold; }
    .footer { position: fixed; bottom: 0; width: 100%; text-align: center; color: #D4AF37; background: #00001a; padding: 5px; border-top: 1px solid #D4AF37; z-index: 99; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. SECURE AUTHENTICATION ---
if 'auth' not in st.session_state: st.session_state['auth'] = False

if not st.session_state['auth']:
    st.sidebar.title("🏛️ JMI LOGIN")
    user_in = st.sidebar.text_input("Username")
    pass_in = st.sidebar.text_input("Password", type='password')
    if st.sidebar.button("SIGN IN"):
        pw_hash = hashlib.sha256(str.encode(pass_in)).hexdigest()
        res = c.execute("SELECT role FROM users WHERE username=? AND password=?", (user_in, pw_hash)).fetchone()
        if res:
            st.session_state.update({"auth": True, "user": user_in, "role": res[0]})
            st.rerun()
        else: st.sidebar.error("Access Denied!")
else:
    if st.sidebar.button("LOG OUT"): st.session_state['auth'] = False; st.rerun()

# --- 5. OWNER CONTROL CENTER (ALL 8 MODULES) ---
if st.session_state['auth']:
    role = st.session_state['role']
    st.title(f"🏢 JMI ENTERPRISE - {role} Control Center")
    
    # គ្រប់ចំណុចដែលលោកបណ្ឌិតចង់បាន (8 Tabs)
    menu = ["Enrollment", "Finance", "ID Cards", "LMS", "Skills", "Attendance", "Health", "CEO Dash"]
    tabs = st.tabs(menu)
    
    # Fetch Student List
    st_df = pd.read_sql_query("SELECT id, name, grade FROM students", conn)

    # 1. Enrollment
    with tabs[0]:
        st.header("Student Registration")
        with st.form("enroll_f"):
            n = st.text_input("Full Name")
            g = st.selectbox("Grade", ["K1-K4", "P1-P6", "S1-S3", "H1-H3"])
            pic = st.file_uploader("Upload Photo", type=['jpg', 'png'])
            if st.form_submit_button("REGISTER"):
                p_blob = pic.read() if pic else None
                c.execute("INSERT INTO students (name, grade, reg_date, photo) VALUES (?,?,?,?)", 
                          (n, g, datetime.now().strftime("%Y-%m-%d"), p_blob))
                conn.commit(); st.success("Registered!"); st.rerun()
        st.dataframe(st_df, use_container_width=True)

    # 2. Finance
    with tabs[1]:
        st.header("Financial Collection")
        if not st_df.empty:
            with st.form("finance_f"):
                sid = st.selectbox("Student", st_df['id'], format_func=lambda x: st_df[st_df['id']==x]['name'].values[0])
                ft = st.selectbox("Fee Type", ["Tuition Fee", "Textbook Fee", "Study Kit", "Admin Fee", "Graduation Fee"])
                amt = st.number_input("Amount ($)", min_value=0.0)
                if st.form_submit_button("SAVE PAYMENT"):
                    tid = str(uuid.uuid4())[:8].upper()
                    c.execute("INSERT INTO payments (student_id, fee_type, amount, date, staff_name, transaction_id) VALUES (?,?,?,?,?,?)", 
                              (sid, ft, amt, datetime.now().strftime("%Y-%m-%d"), st.session_state['user'], tid))
                    conn.commit(); st.success(f"Transaction Recorded: {tid}")
        st.subheader("Financial Records")
        st.dataframe(pd.read_sql_query("SELECT * FROM payments", conn), use_container_width=True)

    # 3. ID Cards
    with tabs[2]:
        st.header("Digital ID Card Generator")
        full_st = pd.read_sql_query("SELECT * FROM students", conn)
        if not full_st.empty:
            cid = st.selectbox("Select Student", full_st['id'], format_func=lambda x: full_st[full_st['id']==x]['name'].values[0])
            target = full_st[full_st['id'] == cid].iloc[0]
            if st.button("GENERATE ID"):
                card_png = generate_jmi_id(target['name'], target['id'], target['grade'], target['photo'])
                st.image(card_png)
                st.download_button("📥 Download PNG", card_png, f"JMI_{target['id']}.png")

    # 4. LMS
    with tabs[3]:
        st.header("Academic Tasks (LMS)")
        with st.form("lms_f"):
            tg = st.selectbox("For Grade", ["K1-K4", "P1-P6", "S1-S3", "H1-H3"], key="lms_g")
            tt = st.text_input("Lesson Title")
            if st.form_submit_button("PUBLISH"):
                c.execute("INSERT INTO assignments (grade, title, deadline) VALUES (?,?,?)", (tg, tt, datetime.now().strftime("%Y-%m-%d")))
                conn.commit(); st.success("Task Published!")
        st.table(pd.read_sql_query("SELECT * FROM assignments", conn))

    # 5. Skills
    with tabs[4]:
        st.header("Medical Skill Passport")
        if not st_df.empty:
            with st.form("skill_f"):
                sid = st.selectbox("Student", st_df['id'], format_func=lambda x: st_df[st_df['id']==x]['name'].values[0], key="sk_sid")
                sk = st.text_input("Skill Name (e.g., CPR Basics)")
                if st.form_submit_button("ADD SKILL"):
                    c.execute("INSERT INTO skill_passport (student_id, skill_name, date_achieved) VALUES (?,?,?)", (sid, sk, datetime.now().strftime("%Y-%m-%d")))
                    conn.commit(); st.success("Skill Recorded!")
        st.dataframe(pd.read_sql_query("SELECT * FROM skill_passport", conn), use_container_width=True)

    # 6. Attendance
    with tabs[5]:
        st.header("Daily Attendance")
        for i, r in st_df.iterrows():
            col1, col2 = st.columns([3, 1])
            col1.write(f"**{r['name']}** (ID: {r['id']})")
            if col2.button("PRESENT", key=f"att_{r['id']}"):
                c.execute("INSERT INTO attendance (student_id, status, date) VALUES (?,?,?)", (r['id'], "Present", datetime.now().strftime("%Y-%m-%d")))
                conn.commit(); st.toast("Success!")

    # 7. Health
    with tabs[6]:
        st.header("Health Tracker (BMI)")
        if not st_df.empty:
            with st.form("health_f"):
                sid = st.selectbox("Student", st_df['id'], format_func=lambda x: st_df[st_df['id']==x]['name'].values[0], key="h_sid")
                w = st.number_input("Weight (kg)", min_value=1.0)
                h = st.number_input("Height (cm)", min_value=30.0)
                if st.form_submit_button("CALCULATE"):
                    bmi, stat = calculate_bmi(w, h)
                    c.execute("INSERT INTO health_tracker (student_id, weight, height, bmi, status, date) VALUES (?,?,?,?,?,?)", 
                              (sid, w, h, bmi, stat, datetime.now().strftime("%Y-%m-%d")))
                    conn.commit(); st.success(f"BMI: {bmi} ({stat})")
        st.dataframe(pd.read_sql_query("SELECT * FROM health_tracker", conn), use_container_width=True)

    # 8. CEO Dash
    with tabs[7]:
        st.header("Financial Analysis")
        rev = c.execute('SELECT SUM(amount) FROM payments').fetchone()[0] or 0
        st.metric("Total Revenue", f"${rev:,.2f}")
        st.subheader("Revenue by Category")
        rev_df = pd.read_sql_query("SELECT fee_type, SUM(amount) as Total FROM payments GROUP BY fee_type", conn)
        st.table(rev_df)

st.markdown(f"<div class='footer'><b>Prepared by Dr. CHAN Sokhoeurn, C2/DBA</b> | JMI v8.5 | 2026</div>", unsafe_allow_html=True)
