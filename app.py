import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import uuid
import io
from datetime import datetime
from PIL import Image, ImageDraw, ImageOps

# --- 1. DATABASE & STRUCTURE (Checked & Verified) ---
# បង្កើត Database ថ្មី v7.9 ដើម្បីជៀសវាងការជាន់ទិន្នន័យចាស់ដែលខុស Structure
DATABASE_NAME = 'jmi_enterprise_v7_9.db'
conn = sqlite3.connect(DATABASE_NAME, check_same_thread=False)
c = conn.cursor()

def init_db():
    # តារាងសិស្ស (បន្ថែម Column 'photo' ជាប្រភេទ BLOB)
    c.execute('''CREATE TABLE IF NOT EXISTS students 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, grade TEXT, 
                  reg_date TEXT, photo BLOB)''')
    
    # តារាងហិរញ្ញវត្ថុ (គ្រប់ប្រភេទថ្លៃសិក្សា និងរដ្ឋបាល)
    c.execute('''CREATE TABLE IF NOT EXISTS payments 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, fee_type TEXT, 
                  amount REAL, date TEXT, staff_name TEXT, transaction_id TEXT)''')
    
    # តារាងការងារសិក្សា និងវត្តមាន
    c.execute('CREATE TABLE IF NOT EXISTS attendance (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, status TEXT, date TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS skill_passport (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, skill_name TEXT, date_achieved TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS assignments (id INTEGER PRIMARY KEY AUTOINCREMENT, grade TEXT, title TEXT, deadline TEXT)')
    
    # តារាងអ្នកប្រើប្រាស់ (Users)
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)')
    
    # កំណត់ Default Users (ប្រើ INSERT OR REPLACE ដើម្បីធានាថា Log in បានជានិច្ច)
    roles = [
        ('ceo_admin', 'JMI@CEO', 'Owner'),
        ('academic_prog', 'JMI@ACAD', 'Academic'),
        ('front_desk', 'JMI@FRONT', 'Front Desk'),
        ('teacher_01', 'JMI@TEACH', 'Teacher')
    ]
    for u, p, r in roles:
        p_hash = hashlib.sha256(str.encode(p)).hexdigest()
        c.execute("INSERT OR REPLACE INTO users VALUES (?,?,?)", (u, p_hash, r))
    conn.commit()

init_db()

# --- 2. CORE FUNCTIONS (Photo ID Card) ---
def draw_id_card_v7_9(name, sid, grade, photo_bytes):
    # បង្កើតផ្ទៃកាត ពណ៌ Navy Blue
    card = Image.new('RGB', (450, 280), color='#000033')
    draw = ImageDraw.Draw(card)
    draw.rectangle([10, 10, 440, 270], outline="#D4AF37", width=4)
    
    # បញ្ចូលរូបថតសិស្ស (ប្រសិនបើមាន)
    if photo_bytes:
        try:
            s_img = Image.open(io.BytesIO(photo_bytes))
            s_img = ImageOps.fit(s_img, (100, 120)) 
            card.paste(s_img, (315, 65)) 
            draw.rectangle([310, 60, 420, 190], outline="white", width=2)
        except: pass
        
    # បញ្ចូលអត្ថបទ
    draw.text((30, 30), "JUNIOR MEDICAL INSTITUTE", fill="#D4AF37")
    draw.text((30, 85), f"NAME: {name.upper()}", fill="white")
    draw.text((30, 125), f"STUDENT ID: {sid}", fill="#D4AF37")
    draw.text((30, 165), f"GRADE: {grade}", fill="white")
    draw.text((30, 230), "Prepared by Dr. CHAN Sokhoeurn, C2/DBA", fill="#D4AF37")
    
    buf = io.BytesIO()
    card.save(buf, format='PNG')
    return buf.getvalue()

# --- 3. PREMIUM UI STYLING (Navy & Gold) ---
st.set_page_config(page_title="JMI Enterprise v7.9", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #000033; color: white; }
    [data-testid="stSidebar"] { background-color: #00001a !important; border-right: 2px solid #D4AF37; }
    h1, h2, h3, label, p, .stMarkdown { color: #D4AF37 !important; }
    .stButton>button { background-color: #D4AF37; color: #000033; font-weight: bold; width: 100%; border-radius: 8px; }
    .stTabs [data-baseweb="tab"] { color: #D4AF37 !important; font-weight: bold; font-size: 16px; }
    .footer { position: fixed; bottom: 0; width: 100%; text-align: center; color: #D4AF37; padding: 10px; background: #00001a; border-top: 1px solid #D4AF37; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. SECURE AUTHENTICATION ---
if 'auth' not in st.session_state: st.session_state['auth'] = False

if not st.session_state['auth']:
    st.sidebar.title("🏛️ JMI LOGIN")
    u_in = st.sidebar.text_input("Username")
    p_in = st.sidebar.text_input("Password", type='password')
    l_mode = st.sidebar.selectbox("Access Mode", ["Staff/Faculty", "Parent/Student"])
    
    if st.sidebar.button("SIGN IN"):
        if l_mode == "Staff/Faculty":
            p_hash = hashlib.sha256(str.encode(p_in)).hexdigest()
            res = c.execute("SELECT role FROM users WHERE username=? AND password=?", (u_in, p_hash)).fetchone()
            if res:
                st.session_state.update({"auth": True, "user": u_in, "role": res[0]})
                st.rerun()
            else: st.sidebar.error("Access Denied! ពិនិត្យ Username/Password ឡើងវិញ។")
        else:
            # Login សម្រាប់ Parent: ឈ្មោះសិស្ស ជា User, ID សិស្ស ជា Password
            student = c.execute("SELECT id FROM students WHERE name=? AND id=?", (u_in, p_in)).fetchone()
            if student:
                st.session_state.update({"auth": True, "user": u_in, "role": "Parent", "sid": student[0]})
                st.rerun()
            else: st.sidebar.error("ឈ្មោះសិស្ស ឬលេខ ID មិនត្រឹមត្រូវ!")
else:
    if st.sidebar.button("LOG OUT"): st.session_state['auth'] = False; st.rerun()

# --- 5. SYSTEM MODULES ---
if st.session_state['auth']:
    role = st.session_state['role']
    st.title(f"🏢 JMI MASTER SYSTEM - {role} Panel")
    
    # កំណត់មឺនុយតាម Role
    menu = []
    if role == "Owner": menu = ["Enrollment", "Finance", "ID Cards", "LMS", "Attendance", "CEO Dash"]
    elif role == "Front Desk": menu = ["Enrollment", "Finance", "ID Cards"]
    elif role == "Academic": menu = ["LMS", "Attendance"]
    elif role == "Teacher": menu = ["Attendance", "LMS"]
    elif role == "Parent": menu = ["Profile", "Homework", "Attendance"]

    tabs = st.tabs(menu)
    students_df = pd.read_sql_query("SELECT id, name, grade, reg_date FROM students", conn)

    # --- TAB: ENROLLMENT (With Photo Upload) ---
    if "Enrollment" in menu:
        with tabs[menu.index("Enrollment")]:
            st.header("Student Registration")
            with st.form("reg_form"):
                n = st.text_input("Full Name")
                g = st.selectbox("Grade", ["K1-K4", "P1-P6", "S1-S3", "H1-H3"])
                u_photo = st.file_uploader("Upload Student Photo", type=['jpg', 'png'])
                if st.form_submit_button("REGISTER"):
                    photo_blob = u_photo.read() if u_photo else None
                    c.execute("INSERT INTO students (name, grade, reg_date, photo) VALUES (?,?,?,?)", 
                              (n, g, datetime.now().strftime("%Y-%m-%d"), photo_blob))
                    conn.commit(); st.success(f"Registered! ID: {c.lastrowid}"); st.rerun()
            st.subheader("Master Student Table")
            st.dataframe(students_df, use_container_width=True)

    # --- TAB: FINANCE (All Fee Types Included) ---
    if "Finance" in menu:
        with tabs[menu.index("Finance")]:
            st.header("Fee Management")
            if not students_df.empty:
                with st.form("pay_form"):
                    sid = st.selectbox("Student", students_df['id'], format_func=lambda x: students_df[students_df['id']==x]['name'].values[0])
                    ftype = st.selectbox("Fee Type", ["Tuition Fee", "Textbook Fee (សៀវភៅ)", "Study Kit (ឯកសណ្ឋាន)", "Admin Fee (រដ្ឋបាល)", "Graduation Fee (បញ្ចប់ការសិក្សា)"])
                    amt = st.number_input("Amount ($)", min_value=0.0)
                    if st.form_submit_button("PAY NOW"):
                        tid = str(uuid.uuid4())[:8].upper()
                        c.execute("INSERT INTO payments (student_id, fee_type, amount, date, staff_name, transaction_id) VALUES (?,?,?,?,?,?)", 
                                  (sid, ftype, amt, datetime.now().strftime("%Y-%m-%d"), st.session_state['user'], tid))
                        conn.commit(); st.success(f"Transaction Recorded: {tid}")
            st.subheader("Financial Records")
            pay_log = pd.read_sql_query("SELECT p.transaction_id, s.name, p.fee_type, p.amount, p.date FROM payments p JOIN students s ON p.student_id = s.id", conn)
            st.dataframe(pay_log, use_container_width=True)

    # --- TAB: ID CARDS (Checked) ---
    if "ID Cards" in menu:
        with tabs[menu.index("ID Cards")]:
            st.header("Card Center")
            full_st = pd.read_sql_query("SELECT * FROM students", conn)
            if not full_st.empty:
                sel_id = st.selectbox("Select Student", full_st['id'], format_func=lambda x: full_st[full_st['id']==x]['name'].values[0])
                target = full_st[full_st['id'] == sel_id].iloc[0]
                if st.button("PREVIEW ID CARD"):
                    card_img = draw_id_card_v7_9(target['name'], target['id'], target['grade'], target['photo'])
                    st.image(card_img)
                    st.download_button("📥 Download PNG", card_img, f"JMI_{target['id']}.png", "image/png")

    # --- TAB: ATTENDANCE ---
    if "Attendance" in menu:
        with tabs[menu.index("Attendance")]:
            st.header("Daily Roll Call")
            for i, r in students_df.iterrows():
                col1, col2 = st.columns([3, 1])
                col1.write(f"**{r['name']}** (ID: {r['id']})")
                if col2.button("PRESENT", key=f"att_{r['id']}"):
                    c.execute("INSERT INTO attendance (student_id, status, date) VALUES (?,?,?)", (r['id'], "Present", datetime.now().strftime("%Y-%m-%d")))
                    conn.commit(); st.toast("Attendance Saved!")

    # --- TAB: CEO DASHBOARD ---
    if "CEO Dash" in menu:
        with tabs[menu.index("CEO Dash")]:
            st.header("Financial Overview")
            total = c.execute('SELECT SUM(amount) FROM payments').fetchone()[0] or 0
            st.metric("Total School Revenue", f"${total:,.2f}")
            st.subheader("Income by Category")
            rev_cat = pd.read_sql_query("SELECT fee_type, SUM(amount) as Total FROM payments GROUP BY fee_type", conn)
            st.table(rev_cat)

st.markdown(f"<div class='footer'><b>Prepared by Dr. CHAN Sokhoeurn, C2/DBA</b> | JMI MASTER v7.9 | 2026</div>", unsafe_allow_html=True)
