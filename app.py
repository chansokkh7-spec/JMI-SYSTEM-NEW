import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import uuid
import io
from datetime import datetime
from PIL import Image, ImageDraw, ImageOps

# --- 1. DATABASE CONFIGURATION ---
# បង្កើត Database ថ្មី v8.0 ដើម្បីឱ្យ Structure ត្រឹមត្រូវ 100%
DB_NAME = 'jmi_enterprise_v8_0.db'
conn = sqlite3.connect(DB_NAME, check_same_thread=False)
c = conn.cursor()

def init_db():
    # តារាងសិស្ស (មានរូបថត)
    c.execute('''CREATE TABLE IF NOT EXISTS students 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, grade TEXT, 
                  reg_date TEXT, photo BLOB)''')
    
    # តារាងហិរញ្ញវត្ថុ (បង់ប្រាក់ ៥ ប្រភេទ)
    c.execute('''CREATE TABLE IF NOT EXISTS payments 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, fee_type TEXT, 
                  amount REAL, date TEXT, staff_name TEXT, transaction_id TEXT)''')
    
    # តារាងវត្តមាន និងកិច្ចការសាលា
    c.execute('CREATE TABLE IF NOT EXISTS attendance (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, status TEXT, date TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS assignments (id INTEGER PRIMARY KEY AUTOINCREMENT, grade TEXT, title TEXT, deadline TEXT)')
    
    # តារាងអ្នកប្រើប្រាស់ (Users)
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)')
    
    # បង្កើត User លំនាំដើម (Owner & Front Desk)
    # ប្រើ INSERT OR REPLACE ដើម្បីកុំឱ្យបាត់ Role នៅពេល Update កូដ
    default_users = [
        ('ceo_admin', 'JMI@CEO', 'Owner'),
        ('front_desk', 'JMI@FRONT', 'Front Desk'),
        ('teacher_01', 'JMI@TEACH', 'Teacher')
    ]
    for u, p, r in default_users:
        p_hash = hashlib.sha256(str.encode(p)).hexdigest()
        c.execute("INSERT OR REPLACE INTO users VALUES (?,?,?)", (u, p_hash, r))
    conn.commit()

init_db()

# --- 2. ID CARD GENERATOR WITH PHOTO ---
def generate_id_card(name, sid, grade, photo_bytes):
    card = Image.new('RGB', (450, 280), color='#000033')
    draw = ImageDraw.Draw(card)
    # Frame Gold
    draw.rectangle([10, 10, 440, 270], outline="#D4AF37", width=5)
    
    # បញ្ចូលរូបថតសិស្ស
    if photo_bytes:
        try:
            img = Image.open(io.BytesIO(photo_bytes))
            img = ImageOps.fit(img, (110, 130))
            card.paste(img, (310, 60))
            draw.rectangle([305, 55, 425, 195], outline="white", width=2)
        except: pass
        
    # បញ្ចូលអត្ថបទព័ត៌មាន
    draw.text((30, 30), "JUNIOR MEDICAL INSTITUTE", fill="#D4AF37")
    draw.text((30, 85), f"NAME: {name.upper()}", fill="white")
    draw.text((30, 130), f"STUDENT ID: {sid}", fill="#D4AF37")
    draw.text((30, 175), f"GRADE: {grade}", fill="white")
    draw.text((30, 235), "Prepared by Dr. CHAN Sokhoeurn, C2/DBA", fill="#D4AF37")
    
    buf = io.BytesIO()
    card.save(buf, format='PNG')
    return buf.getvalue()

# --- 3. PREMIUM UI DESIGN ---
st.set_page_config(page_title="JMI Master System v8.0", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #000033; color: white; }
    [data-testid="stSidebar"] { background-color: #00001a !important; border-right: 2px solid #D4AF37; }
    h1, h2, h3, label, p, .stMarkdown { color: #D4AF37 !important; }
    .stButton>button { background-color: #D4AF37; color: #000033; font-weight: bold; border-radius: 8px; border: none; }
    .stTabs [data-baseweb="tab"] { color: #D4AF37 !important; font-weight: bold; font-size: 18px; }
    .footer { position: fixed; bottom: 0; width: 100%; text-align: center; color: #D4AF37; padding: 10px; background: #00001a; border-top: 1px solid #D4AF37; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. LOGIN SYSTEM ---
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
        else: st.sidebar.error("Invalid Credentials!")
else:
    if st.sidebar.button("LOG OUT"): st.session_state['auth'] = False; st.rerun()

# --- 5. MAIN CONTENT ---
if st.session_state['auth']:
    role = st.session_state['role']
    st.title(f"🏢 JMI ENTERPRISE - {role} Portal")
    
    # កំណត់ Menu តាមតួនាទី
    menu = []
    if role == "Owner": menu = ["Enrollment", "Finance", "ID Cards", "LMS", "Attendance", "CEO Dash"]
    elif role == "Front Desk": menu = ["Enrollment", "Finance", "ID Cards"]
    else: menu = ["Attendance", "LMS"]

    tabs = st.tabs(menu)
    students = pd.read_sql_query("SELECT id, name, grade, reg_date FROM students", conn)

    # --- TAB: ENROLLMENT ---
    if "Enrollment" in menu:
        with tabs[menu.index("Enrollment")]:
            st.header("Register Student")
            with st.form("reg"):
                name = st.text_input("Full Name")
                grade = st.selectbox("Grade", ["K1-K4", "P1-P6", "S1-S3", "H1-H3"])
                photo = st.file_uploader("Upload Student Photo", type=['jpg', 'png'])
                if st.form_submit_button("REGISTER"):
                    p_blob = photo.read() if photo else None
                    c.execute("INSERT INTO students (name, grade, reg_date, photo) VALUES (?,?,?,?)", 
                              (name, grade, datetime.now().strftime("%Y-%m-%d"), p_blob))
                    conn.commit(); st.success("Success!"); st.rerun()
            st.subheader("Student Registry")
            st.dataframe(students, use_container_width=True)

    # --- TAB: FINANCE ---
    if "Finance" in menu:
        with tabs[menu.index("Finance")]:
            st.header("Payment Center")
            if not students.empty:
                with st.form("pay"):
                    sid = st.selectbox("Student", students['id'], format_func=lambda x: students[students['id']==x]['name'].values[0])
                    ftype = st.selectbox("Fee Type", ["Tuition Fee", "Textbook Fee", "Study Kit", "Admin Fee", "Graduation Fee"])
                    amt = st.number_input("Amount ($)", min_value=0.0)
                    if st.form_submit_button("SAVE PAYMENT"):
                        tid = str(uuid.uuid4())[:8].upper()
                        c.execute("INSERT INTO payments (student_id, fee_type, amount, date, staff_name, transaction_id) VALUES (?,?,?,?,?,?)", 
                                  (sid, ftype, amt, datetime.now().strftime("%Y-%m-%d"), st.session_state['user'], tid))
                        conn.commit(); st.success(f"Receipt: {tid}")
            st.subheader("Transactions")
            p_log = pd.read_sql_query("SELECT p.transaction_id, s.name, p.fee_type, p.amount, p.date FROM payments p JOIN students s ON p.student_id = s.id", conn)
            st.dataframe(p_log, use_container_width=True)

    # --- TAB: ID CARDS ---
    if "ID Cards" in menu:
        with tabs[menu.index("ID Cards")]:
            st.header("Card Generator")
            all_st = pd.read_sql_query("SELECT * FROM students", conn)
            if not all_st.empty:
                sel = st.selectbox("Student", all_st['id'], format_func=lambda x: all_st[all_st['id']==x]['name'].values[0])
                target = all_st[all_st['id'] == sel].iloc[0]
                if st.button("PREVIEW ID CARD"):
                    id_png = generate_id_card(target['name'], target['id'], target['grade'], target['photo'])
                    st.image(id_png)
                    st.download_button("📥 Download", id_png, f"JMI_{target['id']}.png", "image/png")

    # --- TAB: LMS ---
    if "LMS" in menu:
        with tabs[menu.index("LMS")]:
            st.header("Learning Management System")
            with st.form("lms"):
                t_grade = st.selectbox("Assign to Grade", ["K1-K4", "P1-P6", "S1-S3", "H1-H3"])
                t_title = st.text_input("Lesson Title")
                if st.form_submit_button("PUBLISH"):
                    c.execute("INSERT INTO assignments (grade, title, deadline) VALUES (?,?,?)", (t_grade, t_title, datetime.now().strftime("%Y-%m-%d")))
                    conn.commit(); st.success("Published!")
            st.dataframe(pd.read_sql_query("SELECT * FROM assignments", conn), use_container_width=True)

    # --- TAB: ATTENDANCE ---
    if "Attendance" in menu:
        with tabs[menu.index("Attendance")]:
            st.header("Attendance List")
            for i, r in students.iterrows():
                c1, c2 = st.columns([3, 1])
                c1.write(f"**{r['name']}**")
                if c2.button("PRESENT", key=f"a_{r['id']}"):
                    c.execute("INSERT INTO attendance (student_id, status, date) VALUES (?,?,?)", (r['id'], "Present", datetime.now().strftime("%Y-%m-%d")))
                    conn.commit(); st.toast("Saved!")

    # --- TAB: CEO DASHBOARD ---
    if "CEO Dash" in menu:
        with tabs[menu.index("CEO Dash")]:
            st.header("Executive Summary")
            total = c.execute('SELECT SUM(amount) FROM payments').fetchone()[0] or 0
            st.metric("Total Revenue", f"${total:,.2f}")
            st.subheader("Revenue by Category")
            rev = pd.read_sql_query("SELECT fee_type, SUM(amount) as Total FROM payments GROUP BY fee_type", conn)
            st.table(rev)

st.markdown(f"<div class='footer'><b>Prepared by Dr. CHAN Sokhoeurn, C2/DBA</b> | JMI MASTER v8.0 | 2026</div>", unsafe_allow_html=True)
