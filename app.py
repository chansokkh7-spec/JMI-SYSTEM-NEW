import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import uuid
import io
from datetime import datetime
from PIL import Image, ImageDraw, ImageOps

# --- 1. DATABASE & STRUCTURE (With Photo Support) ---
DATABASE_NAME = 'jmi_enterprise_v7_8.db'
conn = sqlite3.connect(DATABASE_NAME, check_same_thread=False)
c = conn.cursor()

def init_db():
    # Added 'photo' column (BLOB) to store image data
    c.execute('''CREATE TABLE IF NOT EXISTS students 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, grade TEXT, 
                  reg_date TEXT, photo BLOB)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS payments 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, fee_type TEXT, 
                  amount REAL, date TEXT, staff_name TEXT, transaction_id TEXT)''')
    
    c.execute('CREATE TABLE IF NOT EXISTS attendance (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, status TEXT, date TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS skill_passport (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, skill_name TEXT, date_achieved TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS assignments (id INTEGER PRIMARY KEY AUTOINCREMENT, grade TEXT, title TEXT, deadline TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)')
    
    # Default Roles
    roles = [('ceo_admin', 'JMI@CEO', 'Owner'), ('front_desk', 'JMI@FRONT', 'Front Desk')]
    for u, p, r in roles:
        p_hash = hashlib.sha256(str.encode(p)).hexdigest()
        c.execute("INSERT OR IGNORE INTO users VALUES (?,?,?)", (u, p_hash, r))
    conn.commit()

init_db()

# --- 2. ID CARD GENERATOR WITH PHOTO ---
def generate_photo_id(name, sid, grade, photo_bytes):
    # Base Card
    width, height = 450, 280
    card = Image.new('RGB', (width, height), color='#000033')
    draw = ImageDraw.Draw(card)
    draw.rectangle([10, 10, 440, 270], outline="#D4AF37", width=4)
    
    # Process Photo
    if photo_bytes:
        student_img = Image.open(io.BytesIO(photo_bytes))
        student_img = ImageOps.fit(student_img, (100, 120)) # Resize to fit
        card.paste(student_img, (310, 60)) # Position photo on the right
    
    # Text
    draw.text((30, 30), "JUNIOR MEDICAL INSTITUTE", fill="#D4AF37")
    draw.text((30, 80), f"NAME: {name.upper()}", fill="white")
    draw.text((30, 120), f"ID: {sid}", fill="#D4AF37")
    draw.text((30, 160), f"GRADE: {grade}", fill="white")
    draw.text((30, 230), "Authored by Dr. CHAN Sokhoeurn", fill="#D4AF37")
    
    buf = io.BytesIO()
    card.save(buf, format='PNG')
    return buf.getvalue()

# --- 3. UI STYLING ---
st.set_page_config(page_title="JMI Management v7.8", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #000033; color: white; }
    h1, h2, h3, label, p { color: #D4AF37 !important; }
    .stButton>button { background-color: #D4AF37; color: #000033; font-weight: bold; border-radius: 10px; }
    .footer { position: fixed; bottom: 0; width: 100%; text-align: center; color: #D4AF37; background: #00001a; padding: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. AUTHENTICATION LOGIC ---
if 'auth' not in st.session_state: st.session_state['auth'] = False

if not st.session_state['auth']:
    st.sidebar.title("JMI LOGIN")
    u_in = st.sidebar.text_input("User")
    p_in = st.sidebar.text_input("Pass", type='password')
    if st.sidebar.button("LOG IN"):
        p_hash = hashlib.sha256(str.encode(p_in)).hexdigest()
        res = c.execute("SELECT role FROM users WHERE username=? AND password=?", (u_in, p_hash)).fetchone()
        if res:
            st.session_state.update({"auth": True, "user": u_in, "role": res[0]})
            st.rerun()
else:
    if st.sidebar.button("LOGOUT"): st.session_state['auth'] = False; st.rerun()

# --- 5. MAIN SYSTEM ---
if st.session_state['auth']:
    role = st.session_state['role']
    st.title(f"🏛️ JMI ENTERPRISE - {role} Panel")
    
    menu = ["Enrollment", "Finance", "ID Cards", "LMS", "CEO Dash"] if role == "Owner" else ["Enrollment", "Finance", "ID Cards"]
    tabs = st.tabs(menu)
    
    # MODULE: ENROLLMENT (With Photo Upload)
    if "Enrollment" in menu:
        with tabs[menu.index("Enrollment")]:
            st.header("Register New Student")
            with st.form("enroll_form"):
                n = st.text_input("Student Name")
                g = st.selectbox("Grade", ["K1-K4", "P1-P6", "S1-S3", "H1-H3"])
                uploaded_file = st.file_uploader("Upload Student Photo (JPG/PNG)", type=['jpg', 'png'])
                if st.form_submit_button("SAVE STUDENT"):
                    photo_data = uploaded_file.read() if uploaded_file else None
                    c.execute("INSERT INTO students (name, grade, reg_date, photo) VALUES (?,?,?,?)", 
                              (n, g, datetime.now().strftime("%Y-%m-%d"), photo_data))
                    conn.commit(); st.success("Student Saved Successfully!"); st.rerun()
            
            st.subheader("Student List")
            st_list = pd.read_sql_query("SELECT id, name, grade, reg_date FROM students", conn)
            st.dataframe(st_list, use_container_width=True)

    # MODULE: FINANCE (Detailed Fees)
    if "Finance" in menu:
        with tabs[menu.index("Finance")]:
            st.header("Financial Desk")
            st_df = pd.read_sql_query("SELECT id, name FROM students", conn)
            if not st_df.empty:
                with st.form("pay_f"):
                    sid = st.selectbox("Student", st_df['id'], format_func=lambda x: st_df[st_df['id']==x]['name'].values[0])
                    ftype = st.selectbox("Fee", ["Tuition", "Textbooks", "Study Kit", "Admin", "Graduation"])
                    amt = st.number_input("Amount ($)", min_value=0.0)
                    if st.form_submit_button("SUBMIT PAYMENT"):
                        tid = str(uuid.uuid4())[:8].upper()
                        c.execute("INSERT INTO payments (student_id, fee_type, amount, date, staff_name, transaction_id) VALUES (?,?,?,?,?,?)", 
                                  (sid, ftype, amt, datetime.now().strftime("%Y-%m-%d"), st.session_state['user'], tid))
                        conn.commit(); st.success(f"Transaction ID: {tid}")

    # MODULE: ID CARDS (Photo Rendering)
    if "ID Cards" in menu:
        with tabs[menu.index("ID Cards")]:
            st.header("Digital ID Card Generator")
            cards_df = pd.read_sql_query("SELECT id, name, grade, photo FROM students", conn)
            if not cards_df.empty:
                sel_id = st.selectbox("Select Student", cards_df['id'], format_func=lambda x: cards_df[cards_df['id']==x]['name'].values[0])
                target = cards_df[cards_df['id'] == sel_id].iloc[0]
                if st.button("PREVIEW CARD"):
                    card_bytes = generate_photo_id(target['name'], target['id'], target['grade'], target['photo'])
                    st.image(card_bytes)
                    st.download_button("📥 Download Card", card_bytes, f"JMI_{target['id']}.png", "image/png")

st.markdown(f"<div class='footer'><b>Prepared by Dr. CHAN Sokhoeurn, C2/DBA</b> | JMI v7.8</div>", unsafe_allow_html=True)
