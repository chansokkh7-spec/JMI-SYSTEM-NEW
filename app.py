import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import uuid
import io
from datetime import datetime
from PIL import Image, ImageDraw, ImageOps
from fpdf import FPDF 

# --- 1. DATABASE CONFIGURATION ---
DB_NAME = 'jmi_enterprise_v9.db'
conn = sqlite3.connect(DB_NAME, check_same_thread=False)
c = conn.cursor()

def init_db():
    # Enrollment Table (ជាមួយ Custom ID)
    c.execute('''CREATE TABLE IF NOT EXISTS students 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, custom_id TEXT, name TEXT, 
                  grade TEXT, reg_date TEXT, photo BLOB)''')
    # Finance Table
    c.execute('''CREATE TABLE IF NOT EXISTS payments 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id TEXT, fee_type TEXT, 
                  amount REAL, date TEXT, staff_name TEXT, transaction_id TEXT)''')
    # Attendance Table
    c.execute('CREATE TABLE IF NOT EXISTS attendance (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id TEXT, status TEXT, date TEXT)')
    # Skill Passport
    c.execute('CREATE TABLE IF NOT EXISTS skill_passport (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id TEXT, skill_name TEXT, date_achieved TEXT)')
    # Health Table
    c.execute('CREATE TABLE IF NOT EXISTS health_tracker (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id TEXT, weight REAL, height REAL, bmi REAL, status TEXT, date TEXT)')
    # LMS Table
    c.execute('CREATE TABLE IF NOT EXISTS assignments (id INTEGER PRIMARY KEY AUTOINCREMENT, grade TEXT, title TEXT, deadline TEXT)')
    # User Table
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)')
    
    # Default Admin
    admin_pw = hashlib.sha256(str.encode('JMI@CEO')).hexdigest()
    c.execute("INSERT OR REPLACE INTO users VALUES (?,?,?)", ('ceo_admin', admin_pw, 'Owner'))
    conn.commit()

init_db()

# --- 2. PDF & ID CARD TOOLS ---
def create_pdf_report(rev_df, total_rev):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="JUNIOR MEDICAL INSTITUTE (JMI)", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Financial Report - {datetime.now().strftime('%Y-%m-%d')}", ln=True, align='C')
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"TOTAL REVENUE: ${total_rev:,.2f}", ln=True, align='L')
    pdf.ln(5)
    pdf.set_fill_color(212, 175, 55)
    pdf.cell(95, 10, "Fee Category", 1, 0, 'C', True)
    pdf.cell(95, 10, "Total Amount ($)", 1, 1, 'C', True)
    pdf.set_font("Arial", size=10)
    for i, row in rev_df.iterrows():
        pdf.cell(95, 10, str(row['fee_type']), 1)
        pdf.cell(95, 10, f"${row['Total']:,.2f}", 1, 1)
    pdf.ln(10)
    pdf.cell(200, 10, txt="Approved by: Dr. CHAN Sokhoeurn, C2/DBA", ln=True, align='R')
    return pdf.output(dest='S').encode('latin-1')

def generate_jmi_id(name, sid, grade, photo_bytes):
    card = Image.new('RGB', (450, 280), color='#000033')
    draw = ImageDraw.Draw(card)
    draw.rectangle([10, 10, 440, 270], outline="#D4AF37", width=5)
    if photo_bytes:
        try:
            img = Image.open(io.BytesIO(photo_bytes))
            img = ImageOps.fit(img, (110, 130))
            card.paste(img, (310, 60))
        except: pass
    draw.text((30, 30), "JUNIOR MEDICAL INSTITUTE", fill="#D4AF37")
    draw.text((30, 90), f"NAME: {name.upper()}", fill="white")
    draw.text((30, 135), f"ID: {sid}", fill="#D4AF37")
    draw.text((30, 180), f"GRADE: {grade}", fill="white")
    draw.text((30, 235), "Prepared by Dr. CHAN Sokhoeurn, C2/DBA", fill="#D4AF37")
    buf = io.BytesIO()
    card.save(buf, format='PNG')
    return buf.getvalue()

# --- 3. UI STYLING ---
st.set_page_config(page_title="JMI Master Portal v9.0", layout="wide")
st.markdown("<style>.stApp { background-color: #000033; color: white; } h1,h2,h3,label,p { color: #D4AF37 !important; } .stButton>button { background-color: #D4AF37; color: #000033; font-weight: bold; border-radius: 10px; } .stTabs [data-baseweb='tab'] { color: #D4AF37 !important; font-weight: bold; } .footer { position: fixed; bottom: 0; width: 100%; text-align: center; color: #D4AF37; background: #00001a; padding: 5px; border-top: 1px solid #D4AF37; }</style>", unsafe_allow_html=True)

# --- 4. LOGIN LOGIC ---
if 'auth' not in st.session_state: st.session_state['auth'] = False

if not st.session_state['auth']:
    st.sidebar.title("🏛️ JMI LOGIN")
    u_in = st.sidebar.text_input("Username (Name for Parent)")
    p_in = st.sidebar.text_input("Password (ID for Parent)", type='password')
    if st.sidebar.button("SIGN IN"):
        # Check Admin
        pw_hash = hashlib.sha256(str.encode(p_in)).hexdigest()
        admin = c.execute("SELECT role FROM users WHERE username=? AND password=?", (u_in, pw_hash)).fetchone()
        if admin:
            st.session_state.update({"auth": True, "user": u_in, "role": admin[0]})
            st.rerun()
        else:
            # Check Parent/Student (Name + Custom ID)
            student = c.execute("SELECT custom_id FROM students WHERE name=? AND custom_id=?", (u_in, p_in)).fetchone()
            if student:
                st.session_state.update({"auth": True, "user": u_in, "role": "Parent", "sid": student[0]})
                st.rerun()
            else: st.sidebar.error("Invalid Credentials!")
else:
    if st.sidebar.button("LOG OUT"): st.session_state['auth'] = False; st.rerun()

# --- 5. MAIN SYSTEM ---
if st.session_state['auth']:
    role = st.session_state['role']
    st.title(f"🏢 JMI MASTER - {role} Panel")
    
    if role == "Owner":
        menu = ["Enrollment", "Finance", "ID Cards", "LMS", "Skills", "Attendance", "Health", "CEO Dash"]
    else: # Parent View
        menu = ["Student Profile", "Learning Center", "Health & Attendance"]
    
    tabs = st.tabs(menu)
    st_list = pd.read_sql_query("SELECT custom_id, name, grade FROM students", conn)

    if role == "Owner":
        # Enrollment (JMI-0001 Logic)
        with tabs[0]:
            st.header("Register New Student")
            with st.form("reg"):
                n, g = st.text_input("Full Name"), st.selectbox("Grade", ["K1-K4", "P1-P6", "S1-S3", "H1-H3"])
                pic = st.file_uploader("Photo", type=['jpg', 'png'])
                if st.form_submit_button("REGISTER"):
                    last = c.execute("SELECT id FROM students ORDER BY id DESC LIMIT 1").fetchone()
                    nxt = (last[0] + 1) if last else 1
                    cid = f"JMI-{nxt:04d}"
                    p_blob = pic.read() if pic else None
                    c.execute("INSERT INTO students (custom_id, name, grade, reg_date, photo) VALUES (?,?,?,?,?)", (cid, n, g, datetime.now().strftime("%Y-%m-%d"), p_blob))
                    conn.commit(); st.success(f"Success! ID: {cid}"); st.rerun()
            st.dataframe(st_list, use_container_width=True)

        # Finance
        with tabs[1]:
            st.header("Finance Center")
            if not st_list.empty:
                with st.form("pay"):
                    sid = st.selectbox("Student", st_list['custom_id'], format_func=lambda x: st_list[st_list['custom_id']==x]['name'].values[0])
                    ft = st.selectbox("Type", ["Tuition Fee", "Textbook Fee", "Study Kit", "Admin Fee", "Graduation Fee"])
                    amt = st.number_input("Amount ($)", min_value=0.0)
                    if st.form_submit_button("SAVE"):
                        tid = str(uuid.uuid4())[:8].upper()
                        c.execute("INSERT INTO payments (student_id, fee_type, amount, date, staff_name, transaction_id) VALUES (?,?,?,?,?,?)", (sid, ft, amt, datetime.now().strftime("%Y-%m-%d"), st.session_state['user'], tid))
                        conn.commit(); st.success(f"Receipt: {tid}")
            st.dataframe(pd.read_sql_query("SELECT * FROM payments", conn), use_container_width=True)

        # ID Cards
        with tabs[2]:
            st.header("ID Generator")
            all_s = pd.read_sql_query("SELECT * FROM students", conn)
            if not all_s.empty:
                sel = st.selectbox("Select", all_s['custom_id'], format_func=lambda x: all_s[all_s['custom_id']==x]['name'].values[0])
                t = all_s[all_s['custom_id'] == sel].iloc[0]
                if st.button("PREVIEW"):
                    id_img = generate_jmi_id(t['name'], t['custom_id'], t['grade'], t['photo'])
                    st.image(id_img); st.download_button("📥 Download", id_img, f"{t['custom_id']}.png")

        # LMS
        with tabs[3]:
            st.header("Publish Task")
            with st.form("lms"):
                tg, tl = st.selectbox("To Grade", ["K1-K4", "P1-P6", "S1-S3", "H1-H3"]), st.text_input("Title")
                if st.form_submit_button("PUBLISH"):
                    c.execute("INSERT INTO assignments (grade, title, deadline) VALUES (?,?,?)", (tg, tl, datetime.now().strftime("%Y-%m-%d")))
                    conn.commit(); st.success("Done!")
            st.table(pd.read_sql_query("SELECT * FROM assignments", conn))

        # Skills, Attendance, Health (ស្រដៀងគ្នា)
        with tabs[4]: # Skills
            st.header("Skill Passport")
            if not st_list.empty:
                with st.form("sk"):
                    sid, skn = st.selectbox("Student", st_list['custom_id']), st.text_input("Skill")
                    if st.form_submit_button("GRANT"):
                        c.execute("INSERT INTO skill_passport (student_id, skill_name, date_achieved) VALUES (?,?,?)", (sid, skn, datetime.now().strftime("%Y-%m-%d")))
                        conn.commit(); st.success("Added!")

        with tabs[5]: # Attendance
            st.header("Roll Call")
            for i, r in st_list.iterrows():
                col1, col2 = st.columns([3, 1])
                col1.write(f"**{r['name']}** ({r['custom_id']})")
                if col2.button("PRESENT", key=f"a_{r['custom_id']}"):
                    c.execute("INSERT INTO attendance (student_id, status, date) VALUES (?,?,?)", (r['custom_id'], "Present", datetime.now().strftime("%Y-%m-%d")))
                    conn.commit(); st.toast("Saved")

        with tabs[6]: # Health
            st.header("BMI Tracker")
            if not st_list.empty:
                with st.form("h"):
                    sid, w, h = st.selectbox("Student", st_list['custom_id']), st.number_input("Weight"), st.number_input("Height")
                    if st.form_submit_button("SAVE BMI"):
                        bmi = round(w / ((h/100)**2), 2) if h > 0 else 0
                        stat = "Normal" if 18.5 <= bmi <= 24.9 else "Check Up"
                        c.execute("INSERT INTO health_tracker (student_id, weight, height, bmi, status, date) VALUES (?,?,?,?,?,?)", (sid, w, h, bmi, stat, datetime.now().strftime("%Y-%m-%d")))
                        conn.commit(); st.success(f"BMI: {bmi}")

        # CEO Dash with PDF Report
        with tabs[7]:
            st.header("Executive Analytics")
            total = c.execute('SELECT SUM(amount) FROM payments').fetchone()[0] or 0
            st.metric("TOTAL REVENUE", f"${total:,.2f}")
            rev_df = pd.read_sql_query("SELECT fee_type, SUM(amount) as Total FROM payments GROUP BY fee_type", conn)
            st.table(rev_df)
            if not rev_df.empty:
                pdf = create_pdf_report(rev_df, total)
                st.download_button("📥 Print Financial Report (PDF)", pdf, "JMI_Report.pdf", "application/pdf")

    else: # Parent Tabs
        with tabs[0]: 
            st.write(f"Welcome to Student Portal: **{st.session_state['user']}**")
        with tabs[1]:
            st.header("My Assignments")
            tasks = pd.read_sql_query("SELECT * FROM assignments", conn)
            st.table(tasks)

st.markdown(f"<div class='footer'><b>Prepared by Dr. CHAN Sokhoeurn, C2/DBA</b> | JMI v9.0 | 2026</div>", unsafe_allow_html=True)
