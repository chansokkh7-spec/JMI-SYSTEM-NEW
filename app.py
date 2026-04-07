import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import uuid
import io
import os
from datetime import datetime
from PIL import Image, ImageDraw, ImageOps
from fpdf import FPDF 

# --- 1. JMI LOGO & BRANDING ---
# កូដនឹងឆែករក File ឈ្មោះ logo.png ក្នុង Folder ជាមួយ app.py
LOGO_FILE = "logo.png"

def get_jmi_logo():
    if os.path.exists(LOGO_FILE):
        return Image.open(LOGO_FILE)
    else:
        # បង្កើត Logo បណ្តោះអាសន្នបើរក File មិនឃើញ
        img = Image.new('RGBA', (100, 100), (0, 0, 51, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse([5, 5, 95, 95], outline="#D4AF37", width=5)
        return img

# --- 2. DATABASE ARCHITECTURE ---
DB_NAME = 'jmi_enterprise_v10.db'
conn = sqlite3.connect(DB_NAME, check_same_thread=False)
c = conn.cursor()

def init_db():
    c.execute('CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY AUTOINCREMENT, custom_id TEXT, name TEXT, grade TEXT, reg_date TEXT, photo BLOB)')
    c.execute('CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id TEXT, fee_type TEXT, amount REAL, date TEXT, staff_name TEXT, transaction_id TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS attendance (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id TEXT, status TEXT, date TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS skill_passport (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id TEXT, skill_name TEXT, date_achieved TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS health_tracker (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id TEXT, weight REAL, height REAL, bmi REAL, status TEXT, date TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS assignments (id INTEGER PRIMARY KEY AUTOINCREMENT, grade TEXT, title TEXT, deadline TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)')
    
    # Default Admin: user=ceo_admin, pass=JMI@CEO
    admin_pw = hashlib.sha256(str.encode('JMI@CEO')).hexdigest()
    c.execute("INSERT OR REPLACE INTO users VALUES (?,?,?)", ('ceo_admin', admin_pw, 'Owner'))
    conn.commit()

init_db()

# --- 3. CORE TOOLS (PDF & ID CARD) ---
def create_pdf_report(rev_df, total_rev):
    pdf = FPDF()
    pdf.add_page()
    # Header with Logo
    if os.path.exists(LOGO_FILE):
        pdf.image(LOGO_FILE, x=10, y=8, w=25)
    
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="JUNIOR MEDICAL INSTITUTE (JMI)", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Financial Executive Report - {datetime.now().strftime('%Y-%m-%d')}", ln=True, align='C')
    pdf.ln(15)
    pdf.cell(200, 10, txt=f"TOTAL REVENUE: ${total_rev:,.2f}", ln=True, align='L')
    pdf.ln(5)
    pdf.set_fill_color(212, 175, 55) # Gold
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
    
    # Paste Logo
    logo = get_jmi_logo().convert("RGBA")
    logo = ImageOps.fit(logo, (60, 60))
    card.paste(logo, (30, 25), logo)

    if photo_bytes:
        try:
            img = Image.open(io.BytesIO(photo_bytes))
            img = ImageOps.fit(img, (110, 130))
            card.paste(img, (310, 60))
            draw.rectangle([305, 55, 425, 195], outline="white", width=2)
        except: pass
        
    draw.text((100, 40), "JUNIOR MEDICAL INSTITUTE", fill="#D4AF37")
    draw.text((30, 95), f"NAME: {name.upper()}", fill="white")
    draw.text((30, 140), f"ID: {sid}", fill="#D4AF37")
    draw.text((30, 185), f"GRADE: {grade}", fill="white")
    draw.text((30, 240), "Prepared by Dr. CHAN Sokhoeurn, C2/DBA", fill="#D4AF37")
    buf = io.BytesIO()
    card.save(buf, format='PNG')
    return buf.getvalue()

# --- 4. PREMIUM UI ---
st.set_page_config(page_title="JMI Master Portal v10.0", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #000033; color: white; }
    [data-testid="stSidebar"] { background-color: #00001a !important; border-right: 2px solid #D4AF37; }
    h1, h2, h3, label, p { color: #D4AF37 !important; }
    .stButton>button { background-color: #D4AF37; color: #000033; font-weight: bold; width: 100%; border-radius: 10px; }
    .stTabs [data-baseweb="tab"] { color: #D4AF37 !important; font-weight: bold; font-size: 16px; }
    .footer { position: fixed; bottom: 0; width: 100%; text-align: center; color: #D4AF37; background: #00001a; padding: 5px; border-top: 1px solid #D4AF37; z-index: 99; }
    </style>
    """, unsafe_allow_html=True)

# --- 5. AUTHENTICATION ---
if 'auth' not in st.session_state: st.session_state['auth'] = False

if not st.session_state['auth']:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.image(get_jmi_logo(), width=150)
        st.title("JMI ENTERPRISE")
    
    st.sidebar.title("🏛️ ACCESS PORTAL")
    u = st.sidebar.text_input("Username / Student Name")
    p = st.sidebar.text_input("Password / Student ID", type='password')
    
    if st.sidebar.button("SIGN IN"):
        # Admin Login
        phash = hashlib.sha256(str.encode(p)).hexdigest()
        admin = c.execute("SELECT role FROM users WHERE username=? AND password=?", (u, phash)).fetchone()
        if admin:
            st.session_state.update({"auth": True, "user": u, "role": admin[0]})
            st.rerun()
        else:
            # Student/Parent Login
            std = c.execute("SELECT custom_id FROM students WHERE name=? AND custom_id=?", (u, p)).fetchone()
            if std:
                st.session_state.update({"auth": True, "user": u, "role": "Parent", "sid": std[0]})
                st.rerun()
            else: st.sidebar.error("Invalid Access!")
else:
    if st.sidebar.button("LOG OUT"): st.session_state['auth'] = False; st.rerun()

# --- 6. OWNER CONTROL CENTER (8 MODULES) ---
if st.session_state['auth']:
    role = st.session_state['role']
    st.title(f"🏢 JMI SYSTEM - {role} Control")
    
    if role == "Owner":
        menu = ["Enrollment", "Finance", "ID Cards", "LMS", "Skills", "Attendance", "Health", "CEO Dash"]
    else:
        menu = ["My Profile", "Assignments", "Health & Attendance"]
    
    tabs = st.tabs(menu)
    st_df = pd.read_sql_query("SELECT custom_id, name, grade FROM students", conn)

    if role == "Owner":
        # 1. Enrollment
        with tabs[0]:
            st.header("Student Registration")
            with st.form("enroll"):
                n, g = st.text_input("Name"), st.selectbox("Grade", ["K1-K4", "P1-P6", "S1-S3", "H1-H3"])
                pic = st.file_uploader("Photo", type=['png', 'jpg'])
                if st.form_submit_button("REGISTER"):
                    last = c.execute("SELECT id FROM students ORDER BY id DESC LIMIT 1").fetchone()
                    nxt = (last[0] + 1) if last else 1
                    cid = f"JMI-{nxt:04d}"
                    p_blob = pic.read() if pic else None
                    c.execute("INSERT INTO students (custom_id, name, grade, reg_date, photo) VALUES (?,?,?,?,?)", (cid, n, g, datetime.now().strftime("%Y-%m-%d"), p_blob))
                    conn.commit(); st.success(f"Registered: {cid}"); st.rerun()
            st.dataframe(st_df, use_container_width=True)

        # 2. Finance
        with tabs[1]:
            st.header("Financial Collection")
            if not st_df.empty:
                with st.form("pay"):
                    sid = st.selectbox("Student", st_df['custom_id'], format_func=lambda x: st_df[st_df['custom_id']==x]['name'].values[0])
                    ft = st.selectbox("Fee Type", ["Tuition Fee", "Textbook Fee", "Study Kit", "Admin Fee", "Graduation Fee"])
                    amt = st.number_input("Amount ($)", min_value=0.0)
                    if st.form_submit_button("COLLECT PAYMENT"):
                        tid = str(uuid.uuid4())[:8].upper()
                        c.execute("INSERT INTO payments (student_id, fee_type, amount, date, staff_name, transaction_id) VALUES (?,?,?,?,?,?)", (sid, ft, amt, datetime.now().strftime("%Y-%m-%d"), st.session_state['user'], tid))
                        conn.commit(); st.success(f"Receipt Issued: {tid}")
            st.dataframe(pd.read_sql_query("SELECT * FROM payments", conn), use_container_width=True)

        # 3. ID Cards
        with tabs[2]:
            st.header("ID Card Generator")
            all_s = pd.read_sql_query("SELECT * FROM students", conn)
            if not all_s.empty:
                sel = st.selectbox("Select Student", all_s['custom_id'], format_func=lambda x: all_s[all_s['custom_id']==x]['name'].values[0], key="id_sel")
                t = all_s[all_s['custom_id'] == sel].iloc[0]
                if st.button("PREVIEW ID"):
                    card = generate_jmi_id(t['name'], t['custom_id'], t['grade'], t['photo'])
                    st.image(card); st.download_button("📥 Download", card, f"{t['custom_id']}.png")

        # 4. LMS
        with tabs[3]:
            st.header("LMS Management")
            with st.form("lms"):
                tg, tl = st.selectbox("Grade", ["K1-K4", "P1-P6", "S1-S3", "H1-H3"]), st.text_input("Title")
                if st.form_submit_button("PUBLISH TASK"):
                    c.execute("INSERT INTO assignments (grade, title, deadline) VALUES (?,?,?)", (tg, tl, datetime.now().strftime("%Y-%m-%d")))
                    conn.commit(); st.success("Task Published!")
            st.table(pd.read_sql_query("SELECT * FROM assignments", conn))

        # 5. Skills
        with tabs[4]:
            st.header("Skill Passport")
            if not st_df.empty:
                with st.form("sk"):
                    sid, skn = st.selectbox("Student ID", st_df['custom_id'], key="sk_sid"), st.text_input("Medical Skill")
                    if st.form_submit_button("GRANT SKILL"):
                        c.execute("INSERT INTO skill_passport (student_id, skill_name, date_achieved) VALUES (?,?,?)", (sid, skn, datetime.now().strftime("%Y-%m-%d")))
                        conn.commit(); st.success("Skill Awarded!")
            st.dataframe(pd.read_sql_query("SELECT * FROM skill_passport", conn), use_container_width=True)

        # 6. Attendance
        with tabs[5]:
            st.header("Daily Attendance")
            for i, r in st_df.iterrows():
                c1, c2 = st.columns([3, 1])
                c1.write(f"**{r['name']}** ({r['custom_id']})")
                if c2.button("MARK PRESENT", key=f"att_{r['custom_id']}"):
                    c.execute("INSERT INTO attendance (student_id, status, date) VALUES (?,?,?)", (r['custom_id'], "Present", datetime.now().strftime("%Y-%m-%d")))
                    conn.commit(); st.toast(f"Saved for {r['name']}")

        # 7. Health
        with tabs[6]:
            st.header("Medical Tracker")
            if not st_df.empty:
                with st.form("health"):
                    sid, w, h = st.selectbox("Student", st_df['custom_id'], key="h_sid"), st.number_input("Weight (kg)"), st.number_input("Height (cm)")
                    if st.form_submit_button("SAVE BMI"):
                        bmi = round(w / ((h/100)**2), 2) if h > 0 else 0
                        stat = "Normal" if 18.5 <= bmi <= 24.9 else "Consultation Required"
                        c.execute("INSERT INTO health_tracker (student_id, weight, height, bmi, status, date) VALUES (?,?,?,?,?,?)", (sid, w, h, bmi, stat, datetime.now().strftime("%Y-%m-%d")))
                        conn.commit(); st.success(f"BMI recorded: {bmi} ({stat})")
            st.dataframe(pd.read_sql_query("SELECT * FROM health_tracker", conn), use_container_width=True)

        # 8. CEO Dash
        with tabs[7]:
            st.header("Financial Executive Analytics")
            total_rev = c.execute('SELECT SUM(amount) FROM payments').fetchone()[0] or 0
            st.metric("TOTAL SCHOOL REVENUE", f"${total_rev:,.2f}")
            rev_df = pd.read_sql_query("SELECT fee_type, SUM(amount) as Total FROM payments GROUP BY fee_type", conn)
            st.table(rev_df)
            if not rev_df.empty:
                pdf_data = create_pdf_report(rev_df, total_rev)
                st.download_button("📥 Print Executive Report (PDF)", pdf_data, "JMI_CEO_Report.pdf", "application/pdf")

    else: # Parent Access
        with tabs[0]: st.subheader(f"Student: {st.session_state['user']} (ID: {st.session_state['sid']})")
        with tabs[1]: st.table(pd.read_sql_query("SELECT * FROM assignments", conn))

st.markdown(f"<div class='footer'><b>Prepared by Dr. CHAN Sokhoeurn, C2/DBA</b> | JMI Enterprise v10.0 | 2026</div>", unsafe_allow_html=True)
