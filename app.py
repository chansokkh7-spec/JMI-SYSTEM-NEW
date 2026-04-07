import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import uuid
from datetime import datetime

# --- ១. ការរៀបចំមូលដ្ឋានទិន្នន័យ (Database Setup) ---
conn = sqlite3.connect('jmi_school_secure.db', check_same_thread=False)
c = conn.cursor()

# បង្កើតតារាងចាំបាច់ទាំងអស់
c.execute('''CREATE TABLE IF NOT EXISTS students 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, grade TEXT, enrollment_date TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS payments 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, amount REAL, 
              date TEXT, staff_name TEXT, transaction_id TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS activity_logs 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, action TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
conn.commit()

# --- ២. មុខងារសុវត្ថិភាព (Security Functions) ---
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text:
        return hashed_text
    return False

# --- ៣. ការកំណត់សោភ័ណភាព (UI/UX Branding) ---
st.set_page_config(page_title="JMI System | CHAN Sokhoeurn", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    [data-testid="stSidebar"] { background-color: #000080; color: white; }
    .stButton>button { background-color: #000080; color: #FFD700; border-radius: 8px; font-weight: bold; width: 100%; }
    h1, h2 { color: #000080; border-bottom: 2px solid #FFD700; padding-bottom: 10px; }
    .footer { position: fixed; bottom: 0; left: 0; width: 100%; background: white; text-align: center; padding: 10px; font-size: 12px; color: #666; border-top: 1px solid #ddd; z-index: 100; }
    </style>
    """, unsafe_allow_html=True)

# --- ៤. ប្រព័ន្ធ Login ---
st.sidebar.title("🔐 JMI SECURE LOGIN")
user = st.sidebar.text_input("ឈ្មោះអ្នកប្រើប្រាស់ (Username)")
password = st.sidebar.text_input("លេខសម្ងាត់ (Password)", type='password')

# លេខសម្ងាត់គំរូសម្រាប់លោកបណ្ឌិត: JMI@2026
hashed_master_pswd = make_hashes("JMI@2026") 

if st.sidebar.button("LOG IN"):
    if check_hashes(password, hashed_master_pswd):
        st.session_state['logged_in'] = True
        st.session_state['user'] = user
        st.sidebar.success(f"ស្វាគមន៍ {user}!")
    else:
        st.sidebar.error("លេខសម្ងាត់មិនត្រឹមត្រូវ")

# --- ៥. Dashboard ក្រោយពេល Login រួច ---
if st.session_state.get('logged_in'):
    role = st.sidebar.selectbox("ជ្រើសរើសផ្នែកគ្រប់គ្រង (Switch Module):", 
        ["Front Desk (ចុះឈ្មោះ/បង់ប្រាក់)", "Academic (សិក្សាធិការ)", "Owner (របាយការណ៍មេ)"])

    # --- MODULE 1: FRONT DESK ---
    if role == "Front Desk (ចុះឈ្មោះ/បង់ប្រាក់)":
        st.header("🏢 ផ្នែកចុះឈ្មោះ និងហិរញ្ញវត្ថុ")
        
        tab1, tab2 = st.tabs(["ចុះឈ្មោះសិស្ស", "ទទួលការបង់ប្រាក់"])
        
        with tab1:
            with st.form("reg_form"):
                s_name = st.text_input("ឈ្មោះសិស្សពេញលេញ")
                s_grade = st.selectbox("កម្រិតថ្នាក់", ["Basic to Master", "Flyers Master (A2)", "C2 Mastery"])
                if st.form_submit_button("រក្សាទុក"):
                    date_now = datetime.now().strftime("%Y-%m-%d")
                    c.execute("INSERT INTO students (name, grade, enrollment_date) VALUES (?, ?, ?)", (s_name, s_grade, date_now))
                    c.execute("INSERT INTO activity_logs (user, action) VALUES (?, ?)", (st.session_state['user'], f"បានចុះឈ្មោះសិស្សថ្មី: {s_name}"))
                    conn.commit()
                    st.success("បានរក្សាទុកទិន្នន័យសិស្ស!")

        with tab2:
            st.subheader("ចេញវិក្កយបត្រ")
            df_st = pd.read_sql_query("SELECT id, name FROM students", conn)
            if not df_st.empty:
                s_id = st.selectbox("ជ្រើសរើសសិស្ស", df_st['id'], format_func=lambda x: df_st[df_st['id']==x]['name'].values[0])
                amount = st.number_input("ចំនួនទឹកប្រាក់ ($)", min_value=0.0)
                if st.button("បញ្ជាក់ការបង់ប្រាក់"):
                    t_id = str(uuid.uuid4())[:8].upper()
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    c.execute("INSERT INTO payments (student_id, amount, date, staff_name, transaction_id) VALUES (?, ?, ?, ?, ?)",
                              (int(s_id), amount, now, st.session_state['user'], t_id))
                    c.execute("INSERT INTO activity_logs (user, action) VALUES (?, ?)", (st.session_state['user'], f"បានទទួលប្រាក់ ${amount} (Ref: {t_id})"))
                    conn.commit()
                    st.success(f"ការបង់ប្រាក់ជោគជ័យ! លេខប្រតិបត្តិការ: {t_id}")

    # --- MODULE 2: ACADEMIC ---
    elif role == "Academic (សិក្សាធិការ)":
        st.header("🎓 ផ្នែកសិក្សាធិការ")
        st.subheader("បញ្ជីឈ្មោះសិស្សសរុប")
        df_all = pd.read_sql_query("SELECT * FROM students", conn)
        st.dataframe(df_all, use_container_width=True)

    # --- MODULE 3: OWNER DASHBOARD ---
    elif role == "Owner (របាយការណ៍មេ)":
        st.header("📊 របាយការណ៍មេសម្រាប់លោកបណ្ឌិត")
        
        # គណនាចំណូល
        income = c.execute("SELECT SUM(amount) FROM payments").fetchone()[0] or 0
        s_count = c.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        
        col1, col2 = st.columns(2)
        col1.metric("ចំណូលសរុប ($)", f"${income:,.2f}")
        col2.metric("ចំនួនសិស្សសរុប", f"{s_count} នាក់")
        
        st.subheader("📝 ដានសកម្មភាពបុគ្គលិក (Audit Logs)")
        df_logs = pd.read_sql_query("SELECT user, action, timestamp FROM activity_logs ORDER BY id DESC", conn)
        st.table(df_logs)

# --- ៦. Footer Branding ---
st.markdown(f"""
    <div class="footer">
        Prepared by <b>CHAN Sokhoeurn, C2/DBA</b> | School Management System v2.0 (Secure Edition)
    </div>
    """, unsafe_allow_html=True)
