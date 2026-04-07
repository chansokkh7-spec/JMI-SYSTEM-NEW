import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import uuid
import io
from datetime import datetime
from PIL import Image, ImageDraw, ImageOps

# --- 1. DATABASE & ARCHITECTURE (Verified All Tables) ---
DB_NAME = 'jmi_enterprise_v8_5.db'
conn = sqlite3.connect(DB_NAME, check_same_thread=False)
c = conn.cursor()

def init_db():
    # 1. តារាងសិស្ស (រូបថត និងព័ត៌មានមូលដ្ឋាន)
    c.execute('''CREATE TABLE IF NOT EXISTS students 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, grade TEXT, 
                  reg_date TEXT, photo BLOB)''')
    
    # 2. តារាងហិរញ្ញវត្ថុ (បែងចែក ៥ ប្រភេទច្បាស់លាស់)
    c.execute('''CREATE TABLE IF NOT EXISTS payments 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, fee_type TEXT, 
                  amount REAL, date TEXT, staff_name TEXT, transaction_id TEXT)''')
    
    # 3. តារាងវត្តមាន
    c.execute('CREATE TABLE IF NOT EXISTS attendance (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, status TEXT, date TEXT)')
    
    # 4. តារាង Skill Passport (ជំនាញវេជ្ជសាស្ត្រកុមារ)
    c.execute('CREATE TABLE IF NOT EXISTS skill_passport (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, skill_name TEXT, date_achieved TEXT)')
    
    # 5. តារាងតាមដានសុខភាព (Health Tracker & BMI)
    c.execute('CREATE TABLE IF NOT EXISTS health_tracker (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, weight REAL, height REAL, bmi REAL, status TEXT, date TEXT)')
    
    # 6. តារាងកិច្ចការសាលា (LMS)
    c.execute('CREATE TABLE IF NOT EXISTS assignments (id INTEGER PRIMARY KEY AUTOINCREMENT, grade TEXT, title TEXT, deadline TEXT)')
    
    # 7. តារាងអ្នកប្រើប្រាស់
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)')
    
    # បង្កើត User លំនាំដើម (Owner ត្រូវតែឃើញ Menu ទាំងអស់)
    admin_pw = hashlib.sha256(str.encode('JMI@CEO')).hexdigest()
    c.execute("INSERT OR REPLACE INTO users VALUES (?,?,?)", ('ceo_admin', admin_pw, 'Owner'))
    conn.commit()

init_db()

# --- 2. CORE UTILITIES (BMI & ID CARD) ---
def calculate_bmi(w, h):
    if h > 0:
        bmi = round(w / ((h/100)**2), 2)
        status = "Normal" if 18.5 <= bmi <= 24.9 else ("Underweight" if bmi < 18.5 else "Overweight")
        return bmi, status
    return 0, "N/A"

def generate_jmi_id(name, sid, grade, photo_bytes):
    card = Image.new('RGB', (450, 280), color='#000033') # Navy Blue
    draw = ImageDraw.Draw(card)
    draw.rectangle([10, 10, 440, 270], outline="#D4AF37", width=5) # Gold Frame
    
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

# --- 3. UI CUSTOMIZATION ---
st.set_page_config(page_title="JMI Master Portal v8.5", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #000033; color: white; }
    [data-testid="stSidebar"] { background-color: #00001a !important; border-right: 2px solid #D4AF37; }
    h1, h2, h3, label, p { color: #D4AF37 !important; }
    .stButton>button { background-color: #D4AF37; color: #000033; font-weight: bold; width: 100%; border-radius: 10px; }
    .stTabs [data-baseweb="tab"] { color: #D4AF37 !important; font-size: 16px; font-weight: bold; }
    .footer { position: fixed; bottom: 0; width: 100%; text-align: center; color: #D4AF37; background: #00001a; padding: 5px; border-top: 1px solid #D4AF37; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. SECURE ACCESS ---
if 'auth' not in st.session_state: st.session_state['auth'] = False

if not st.session_state['auth']:
    st.sidebar.title("🏛️ JMI LOGIN")
    user = st.sidebar.text_input("Username")
    pw = st.sidebar.text_input("Password", type='password')
    if st.sidebar.button("SIGN IN"):
        pw_hash = hashlib.sha256(str.encode(pw)).hexdigest()
        res = c.execute("SELECT role FROM users WHERE username=? AND password=?", (user, pw_hash)).fetchone()
        if res:
            st.session_state.update({"auth": True, "user": user, "role": res[0]})
            st.rerun()
        else: st.sidebar.error("Invalid Login!")
else:
    if st.sidebar.button("LOG OUT"): st.session_state['auth'] = False; st.rerun()

# --- 5. OWNER PANEL (ALL MODULES) ---
if st.session_state['auth']:
    role = st.session_state['role']
    st.title(f"🏢 JMI ENTERPRISE - {role} Control Center")
    
    # លោកបណ្ឌិតនឹងឃើញមឺនុយទាំង ៨ នេះ (Full Options)
    menu = ["Enrollment", "Finance", "ID Cards", "LMS", "Skills", "Attendance", "Health", "CEO Dash"]
    tabs = st.tabs(menu)
    
    # ទាញទិន្នន័យសិស្សសម្រាប់ប្រើក្នុង Tab នីមួយៗ
    st_list = pd.read_sql_query("SELECT id, name, grade FROM students", conn)

    # --- TAB 1: ENROLLMENT ---
    with tabs[0]:
        st.header("Student Registration")
        with st.form("reg"):
            n = st.text_input("Full Name")
            g = st.selectbox("Grade", ["K1-K4", "P1-P6", "S1-S3", "H1-H3"])
            pic = st.file_uploader("Upload Photo", type=['jpg', 'png'])
            if st.form_submit_button("REGISTER"):
                p_blob = pic.read() if pic else None
                c.execute("INSERT INTO students (name, grade, reg_date, photo) VALUES (?,?,?,?)", 
                          (n, g, datetime.now().strftime("%Y-%m-%d"), p_blob))
                conn.commit(); st.success("Registered!"); st.rerun()
        st.dataframe(st_list, use_container_width=True)

    # --- TAB 2: FINANCE ---
    with tabs[1]:
        st.header("Financial Collection")
        if not st_list.empty:
            with st.form("pay"):
                sid = st.selectbox("Student", st_list['id'], format_func=lambda x: st_list[st_list['id']==x]['name'].values[0])
                ft = st.selectbox("Fee Type", ["Tuition Fee", "Textbook Fee", "Study Kit", "Admin Fee", "Graduation Fee"])
                amt = st.number_input("Amount ($)", min_value=0.0)
                if st.form_submit_button("SAVE PAYMENT"):
                    tid = str(uuid.uuid4())[:8].upper()
                    c.execute("INSERT INTO payments (student_id, fee_type, amount, date, staff_name, transaction_id) VALUES (?,?,?,?,?,?)", 
                              (sid, ft, amt, datetime.now().strftime("%Y-%m-%d"), st.session_state['user'], tid))
                    conn.commit(); st.success(f"Receipt: {tid}")
        st.subheader("Financial History")
        st.dataframe(pd.read_sql_query("SELECT * FROM payments", conn), use_container_width=True)

    # --- TAB 3: ID CARDS ---
    with tabs[2]:
        st.header("Digital ID Card Generator")
        all_data = pd.read_sql_query("SELECT * FROM students", conn)
        if not all_data.empty:
            sel = st.selectbox("Choose Student", all_data['id'], format_func=lambda x: all_data[all_data['id']==x]['name'].values[0], key="id_sel")
            target = all_data[all_data['id'] == sel].iloc[0]
            if st.button("PREVIEW ID"):
                card = generate_jmi_id(target['name'], target['id'], target['grade'], target['photo'])
                st.image(card)
                st.download_button("📥 Download", card, f"JMI_{target['id']}.png")

    # --- TAB 4: LMS ---
    with tabs[3]:
        st.header("Academic Tasks (LMS)")
        with st.form("lms_form"):
            tg = st.selectbox("For Grade", ["K1-K4", "P1-P6", "S1-S3", "H1-H3"])
            tl = st.text_input("Assignment Title")
            if st.form_submit_button("PUBLISH"):
                c.execute("INSERT INTO assignments (grade, title, deadline) VALUES (?,?,?)", (tg, tl, datetime.now().strftime("%Y-%m-%d")))
                conn.commit(); st.success("Task Published!")
        st.table(pd.read_sql_query("SELECT * FROM assignments", conn))

    # --- TAB 5: SKILLS (Passport) ---
    with tabs[4]:
        st.header("Medical Skill Passport")
        if not st_list.empty:
            with st.form("skill_f"):
                ssid = st.selectbox("Student", st_list['id'], format_func=lambda x: st_list[st_list['id']==x]['name'].values[0], key="sk_sel")
                skn = st.text_input("Skill Achieved (e.g., CPR Basics)")
                if st.form_submit_button("GRANT SKILL"):
                    c.execute("INSERT INTO skill_passport (student_id, skill_name, date_achieved) VALUES (?,?,?)", (ssid, skn, datetime.now().strftime("%Y-%m-%d")))
                    conn.commit(); st.success("Skill Added!")
        st.dataframe(pd.read_sql_query("SELECT * FROM skill_passport", conn), use_container_width=True)

    # --- TAB 6: ATTENDANCE ---
    with tabs[5]:
        st.header("Daily Attendance")
        for i, r in st_list.iterrows():
            c1, c2 = st.columns([3, 1])
            c1.write(f"**{r['name']}**")
            if c2.button("MARK PRESENT", key=f"att_{r['id']}"):
                c.execute("INSERT INTO attendance (student_id, status, date) VALUES (?,?,?)", (r['id'], "Present", datetime.now().strftime("%Y-%m-%d")))
                conn.commit(); st.toast("Saved!")

    # --- TAB 7: HEALTH (BMI Tracker) ---
    with tabs[6]:
        st.header("Medical Check-up (BMI)")
        if not st_list.empty:
            with st.form("bmi_f"):
                hsid = st.selectbox("Student", st_list['id'], format_func=lambda x: st_list[st_list['id']==x]['name'].values[0], key="bmi_sel")
                w = st.number_input("Weight (kg)", min_value=1.0)
                h = st.number_input("Height (cm)", min_value=30.0)
                if st.form_submit_button("CALCULATE & SAVE"):
                    bmi, stat = calculate_bmi(w, h)
                    c.execute("INSERT INTO health_tracker (student_id, weight, height, bmi, status, date) VALUES (?,?,?,?,?,?)", 
                              (hsid, w, h, bmi, stat, datetime.now().strftime("%Y-%m-%d")))
                    conn.commit(); st.success(f"BMI: {bmi} ({stat})")
        st.dataframe(pd.read_sql_query("SELECT * FROM health_tracker", conn), use_container_width=True)

    # --- TAB 8: CEO DASHBOARD ---
    with tabs[7]:
        st.header("JMI Analytics")
        rev = c.execute('SELECT SUM(amount) FROM payments').fetchone()[0] or 0
        st.metric("Total Revenue", f"${rev:,.2f}")
        st.subheader("Revenue by Category")
        st.table(pd.read_sql_query("SELECT fee_type, SUM(amount) as Total FROM payments GROUP BY fee_type", conn))

st.markdown(f"<div class='footer'><b>Prepared by Dr. CHAN Sokhoeurn, C2/DBA</b> | JMI v8.5 | 2026</div>", unsafe_allow_html=True)
