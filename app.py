import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import uuid
import io
from datetime import datetime
from PIL import Image, ImageDraw, ImageOps
from fpdf import FPDF  # លោកបណ្ឌិតត្រូវដំឡើង pip install fpdf

# --- 1. DATABASE & ARCHITECTURE ---
DB_NAME = 'jmi_enterprise_v8_7.db'
conn = sqlite3.connect(DB_NAME, check_same_thread=False)
c = conn.cursor()

def init_db():
    c.execute('CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, grade TEXT, reg_date TEXT, photo BLOB)')
    c.execute('CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, fee_type TEXT, amount REAL, date TEXT, staff_name TEXT, transaction_id TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS attendance (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, status TEXT, date TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS skill_passport (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, skill_name TEXT, date_achieved TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS health_tracker (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, weight REAL, height REAL, bmi REAL, status TEXT, date TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS assignments (id INTEGER PRIMARY KEY AUTOINCREMENT, grade TEXT, title TEXT, deadline TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)')
    
    admin_pw = hashlib.sha256(str.encode('JMI@CEO')).hexdigest()
    c.execute("INSERT OR REPLACE INTO users VALUES (?,?,?)", ('ceo_admin', admin_pw, 'Owner'))
    conn.commit()

init_db()

# --- 2. PDF GENERATOR FUNCTION ---
def create_pdf_report(rev_df, total_rev):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    
    # Header
    pdf.cell(200, 10, txt="JUNIOR MEDICAL INSTITUTE (JMI)", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Financial Executive Report - {datetime.now().strftime('%Y-%m-%d')}", ln=True, align='C')
    pdf.ln(10)
    
    # Summary
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt=f"TOTAL REVENUE: ${total_rev:,.2f}", ln=True, align='L')
    pdf.ln(5)
    
    # Table Header
    pdf.set_fill_color(212, 175, 55) # Gold Color
    pdf.cell(95, 10, "Fee Category", 1, 0, 'C', True)
    pdf.cell(95, 10, "Total Amount ($)", 1, 1, 'C', True)
    
    # Table Data
    pdf.set_font("Arial", size=10)
    for index, row in rev_df.iterrows():
        pdf.cell(95, 10, str(row['fee_type']), 1)
        pdf.cell(95, 10, f"${row['Total']:,.2f}", 1, 1)
    
    pdf.ln(20)
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(200, 10, txt="Approved by: Dr. CHAN Sokhoeurn, C2/DBA", ln=True, align='R')
    
    return pdf.output(dest='S').encode('latin-1')

# --- 3. CORE TOOLS (BMI & ID) ---
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
        except: pass
    draw.text((30, 30), "JUNIOR MEDICAL INSTITUTE", fill="#D4AF37")
    draw.text((30, 90), f"NAME: {name.upper()}", fill="white")
    draw.text((30, 135), f"ID: {sid}", fill="#D4AF37")
    draw.text((30, 180), f"GRADE: {grade}", fill="white")
    draw.text((30, 235), "Prepared by Dr. CHAN Sokhoeurn, C2/DBA", fill="#D4AF37")
    buf = io.BytesIO()
    card.save(buf, format='PNG')
    return buf.getvalue()

# --- 4. UI & LOGIN ---
st.set_page_config(page_title="JMI Master Portal v8.7", layout="wide")
st.markdown("<style>.stApp { background-color: #000033; color: white; } h1, h2, h3, label, p { color: #D4AF37 !important; } .stButton>button { background-color: #D4AF37; color: #000033; font-weight: bold; width: 100%; border-radius: 10px; } .stTabs [data-baseweb='tab'] { color: #D4AF37 !important; font-weight: bold; } .footer { position: fixed; bottom: 0; width: 100%; text-align: center; color: #D4AF37; background: #00001a; padding: 5px; border-top: 1px solid #D4AF37; }</style>", unsafe_allow_html=True)

if 'auth' not in st.session_state: st.session_state['auth'] = False
if not st.session_state['auth']:
    st.sidebar.title("🏛️ JMI LOGIN")
    u = st.sidebar.text_input("Username")
    p = st.sidebar.text_input("Password", type='password')
    if st.sidebar.button("SIGN IN"):
        pw_hash = hashlib.sha256(str.encode(p)).hexdigest()
        res = c.execute("SELECT role FROM users WHERE username=? AND password=?", (u, pw_hash)).fetchone()
        if res: st.session_state.update({"auth": True, "user": u, "role": res[0]}); st.rerun()
else:
    if st.sidebar.button("LOG OUT"): st.session_state['auth'] = False; st.rerun()

# --- 5. OWNER CONTROL CENTER ---
if st.session_state['auth']:
    st.title(f"🏢 JMI ENTERPRISE - {st.session_state['role']} Control Center")
    menu = ["Enrollment", "Finance", "ID Cards", "LMS", "Skills", "Attendance", "Health", "CEO Dash"]
    tabs = st.tabs(menu)
    st_df = pd.read_sql_query("SELECT id, name, grade FROM students", conn)

    # Enrollment, Finance, ID Cards, LMS, Skills, Attendance, Health (រក្សារចនាសម្ព័ន្ធដូចមុន)
    with tabs[0]:
        with st.form("reg"):
            n, g = st.text_input("Full Name"), st.selectbox("Grade", ["K1-K4", "P1-P6", "S1-S3", "H1-H3"])
            pic = st.file_uploader("Upload Photo", type=['jpg', 'png'])
            if st.form_submit_button("REGISTER"):
                p_blob = pic.read() if pic else None
                c.execute("INSERT INTO students (name, grade, reg_date, photo) VALUES (?,?,?,?)", (n, g, datetime.now().strftime("%Y-%m-%d"), p_blob))
                conn.commit(); st.success("Registered!"); st.rerun()

    with tabs[1]:
        if not st_df.empty:
            with st.form("pay"):
                sid = st.selectbox("Student", st_df['id'], format_func=lambda x: st_df[st_df['id']==x]['name'].values[0])
                ft = st.selectbox("Fee Type", ["Tuition Fee", "Textbook Fee", "Study Kit", "Admin Fee", "Graduation Fee"])
                amt = st.number_input("Amount ($)", min_value=0.0)
                if st.form_submit_button("SAVE PAYMENT"):
                    tid = str(uuid.uuid4())[:8].upper()
                    c.execute("INSERT INTO payments (student_id, fee_type, amount, date, staff_name, transaction_id) VALUES (?,?,?,?,?,?)", (sid, ft, amt, datetime.now().strftime("%Y-%m-%d"), st.session_state['user'], tid))
                    conn.commit(); st.success(f"Receipt: {tid}")
        st.dataframe(pd.read_sql_query("SELECT * FROM payments", conn), use_container_width=True)

    with tabs[2]:
        all_data = pd.read_sql_query("SELECT * FROM students", conn)
        if not all_data.empty:
            cid = st.selectbox("Select Student", all_data['id'], format_func=lambda x: all_data[all_data['id']==x]['name'].values[0])
            target = all_data[all_data['id'] == cid].iloc[0]
            if st.button("GENERATE ID"):
                card = generate_jmi_id(target['name'], target['id'], target['grade'], target['photo'])
                st.image(card); st.download_button("📥 Download", card, f"JMI_{target['id']}.png")

    with tabs[3]:
        with st.form("lms"):
            tg, tt = st.selectbox("Grade", ["K1-K4", "P1-P6", "S1-S3", "H1-H3"]), st.text_input("Lesson Title")
            if st.form_submit_button("PUBLISH"):
                c.execute("INSERT INTO assignments (grade, title, deadline) VALUES (?,?,?)", (tg, tt, datetime.now().strftime("%Y-%m-%d")))
                conn.commit(); st.success("Task Published!")
        st.table(pd.read_sql_query("SELECT * FROM assignments", conn))

    with tabs[4]:
        if not st_df.empty:
            with st.form("skill"):
                sid, sk = st.selectbox("Student", st_df['id'], format_func=lambda x: st_df[st_df['id']==x]['name'].values[0]), st.text_input("Skill")
                if st.form_submit_button("ADD SKILL"):
                    c.execute("INSERT INTO skill_passport (student_id, skill_name, date_achieved) VALUES (?,?,?)", (sid, sk, datetime.now().strftime("%Y-%m-%d")))
                    conn.commit(); st.success("Skill Recorded!")
        st.dataframe(pd.read_sql_query("SELECT * FROM skill_passport", conn), use_container_width=True)

    with tabs[5]:
        for i, r in st_df.iterrows():
            c1, c2 = st.columns([3, 1])
            c1.write(f"**{r['name']}**")
            if c2.button("PRESENT", key=f"att_{r['id']}"):
                c.execute("INSERT INTO attendance (student_id, status, date) VALUES (?,?,?)", (r['id'], "Present", datetime.now().strftime("%Y-%m-%d")))
                conn.commit(); st.toast("Success!")

    with tabs[6]:
        if not st_df.empty:
            with st.form("health"):
                sid, w, h = st.selectbox("Student", st_df['id'], format_func=lambda x: st_df[st_df['id']==x]['name'].values[0]), st.number_input("Weight (kg)"), st.number_input("Height (cm)")
                if st.form_submit_button("SAVE BMI"):
                    bmi, stat = calculate_bmi(w, h)
                    c.execute("INSERT INTO health_tracker (student_id, weight, height, bmi, status, date) VALUES (?,?,?,?,?,?)", (sid, w, h, bmi, stat, datetime.now().strftime("%Y-%m-%d")))
                    conn.commit(); st.success(f"BMI: {bmi}")
        st.dataframe(pd.read_sql_query("SELECT * FROM health_tracker", conn), use_container_width=True)

    # --- TAB 8: CEO DASHBOARD (With PDF Export) ---
    with tabs[7]:
        st.header("Financial Executive Analytics")
        total_rev = c.execute('SELECT SUM(amount) FROM payments').fetchone()[0] or 0
        st.metric("TOTAL SCHOOL REVENUE", f"${total_rev:,.2f}")
        
        rev_df = pd.read_sql_query("SELECT fee_type, SUM(amount) as Total FROM payments GROUP BY fee_type", conn)
        st.subheader("Revenue by Category")
        st.table(rev_df)
        
        st.markdown("---")
        st.subheader("📊 Report Actions")
        if not rev_df.empty:
            pdf_data = create_pdf_report(rev_df, total_rev)
            st.download_button(
                label="📥 Print Financial Report (PDF)",
                data=pdf_data,
                file_name=f"JMI_Report_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf"
            )
        else:
            st.warning("No data available to generate report.")

st.markdown(f"<div class='footer'><b>Prepared by Dr. CHAN Sokhoeurn, C2/DBA</b> | JMI v8.7 | 2026</div>", unsafe_allow_html=True)
