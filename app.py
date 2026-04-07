import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import uuid
from datetime import datetime

# --- 1. DATABASE SETUP ---
DATABASE_NAME = 'jmi_final_v6_1.db'
conn = sqlite3.connect(DATABASE_NAME, check_same_thread=False)
c = conn.cursor()

def init_db():
    # គ្រប់គ្រងសិស្ស និងការបង់ប្រាក់
    c.execute('CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, grade TEXT, reg_date TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, amount REAL, date TEXT, staff_name TEXT, transaction_id TEXT)')
    
    # គ្រប់គ្រងវត្តមាន និងជំនាញ (Skill Passport)
    c.execute('CREATE TABLE IF NOT EXISTS attendance (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, status TEXT, date TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS skill_passport (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, skill_name TEXT, date_achieved TEXT)')
    
    # សុខភាព មេរៀន និងទំនិញ
    c.execute('CREATE TABLE IF NOT EXISTS health_tracker (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, weight REAL, height REAL, diet_note TEXT, date TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS curriculum (id INTEGER PRIMARY KEY AUTOINCREMENT, level TEXT, topic TEXT, link TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS inventory (id INTEGER PRIMARY KEY AUTOINCREMENT, item_name TEXT, stock INTEGER, price REAL)')
    
    # ប្រព័ន្ធសុវត្ថិភាព
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)')
    
    # បង្កើត Admin (User: admin | Pass: JMI@2026)
    admin_hash = hashlib.sha256(str.encode("JMI@2026")).hexdigest()
    c.execute("INSERT OR IGNORE INTO users VALUES (?,?,?)", ('admin', admin_hash, 'Owner'))
    conn.commit()

init_db()

# --- 2. PREMIUM UI STYLING (Navy & Gold) ---
st.set_page_config(page_title="JMI Portal | CHAN Sokhoeurn", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #000033; }
    [data-testid="stSidebar"] { background-color: #00001a !important; border-right: 2px solid #D4AF37; }
    h1, h2, h3, label, p, span, .stMarkdown { color: #D4AF37 !important; }
    .stButton>button { background-color: #D4AF37; color: #000033; border-radius: 8px; font-weight: bold; border: 1px solid #FFD700; width: 100%; }
    .stTabs [data-baseweb="tab"] { color: #D4AF37 !important; font-size: 14px; font-weight: bold; }
    .footer { position: fixed; bottom: 0; left: 0; width: 100%; background-color: #00001a; text-align: center; padding: 5px; color: #D4AF37; border-top: 1px solid #D4AF37; z-index: 100; }
    input, select, textarea { background-color: #000055 !important; color: white !important; border: 1px solid #D4AF37 !important; }
    div[data-testid="stMetricValue"] { color: #D4AF37 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. AUTHENTICATION LOGIC ---
if 'auth' not in st.session_state: st.session_state['auth'] = False

if not st.session_state['auth']:
    st.sidebar.markdown("<h2 style='text-align:center;'>JMI LOGIN</h2>", unsafe_allow_html=True)
    u = st.sidebar.text_input("Username")
    p = st.sidebar.text_input("Password", type='password')
    if st.sidebar.button("ENTER SYSTEM"):
        input_hash = hashlib.sha256(str.encode(p)).hexdigest()
        res = c.execute("SELECT password, role FROM users WHERE username=?", (u,)).fetchone()
        if res and input_hash == res[0]:
            st.session_state.update({"auth": True, "user": u, "role": res[1]})
            st.rerun()
        else: st.sidebar.error("⚠️ ព័ត៌មានមិនត្រឹមត្រូវ")
else:
    st.sidebar.success(f"សួស្តី {st.session_state['user']} ({st.session_state['role']})")
    if st.sidebar.button("LOGOUT"):
        st.session_state['auth'] = False
        st.rerun()

# --- 4. MAIN APPLICATION ---
if st.session_state['auth']:
    role = st.session_state['role']
    st.title("🏛️ JMI MASTER SYSTEM v6.1")
    
    # រៀបចំ Tabs តាមតម្រូវការលោកបណ្ឌិត
    menu = ["📝 Enrollment", "💰 Payments", "📅 Attendance", "📜 Skill Passport", "🧬 Curriculum", "🍎 Health", "🛒 Inventory"]
    if role == "Owner": menu.append("📊 CEO Dashboard")
    tabs = st.tabs(menu)

    # ទទួលបានទិន្នន័យសិស្សសម្រាប់ប្រើប្រាស់គ្រប់ Tab
    sts_df = pd.read_sql_query("SELECT id, name, grade FROM students", conn)

    # --- TAB: ENROLLMENT ---
    with tabs[0]:
        st.header("ការចុះឈ្មោះសិស្សថ្មី")
        with st.form("reg_form"):
            n = st.text_input("ឈ្មោះពេញ")
            g = st.selectbox("កម្រិតសិក្សា", ["K1-K4", "P1-P6", "S1-S3", "H1-H3", "PUF1-PUF2"])
            if st.form_submit_button("ចុះឈ្មោះ"):
                if n:
                    c.execute("INSERT INTO students (name, grade, reg_date) VALUES (?,?,?)", (n, g, datetime.now().strftime("%Y-%m-%d")))
                    conn.commit()
                    st.success(f"ចុះឈ្មោះ {n} រួចរាល់!")
                    st.rerun()
        st.subheader("បញ្ជីសិស្សថ្មីៗ")
        st.dataframe(pd.read_sql_query("SELECT * FROM students ORDER BY id DESC LIMIT 10", conn), use_container_width=True)

    # --- TAB: PAYMENTS ---
    with tabs[1]:
        st.header("ការគ្រប់គ្រងហិរញ្ញវត្ថុ")
        if not sts_df.empty:
            with st.expander("បញ្ចូលការបង់ប្រាក់"):
                sid = st.selectbox("ជ្រើសរើសសិស្ស", sts_df['id'], format_func=lambda x: sts_df[sts_df['id']==x]['name'].values[0], key="p_sid")
                amt = st.number_input("ចំនួនទឹកប្រាក់ ($)", min_value=0.0)
                if st.button("បញ្ជាក់ការបង់ប្រាក់"):
                    tid = str(uuid.uuid4())[:8].upper()
                    c.execute("INSERT INTO payments (student_id, amount, date, staff_name, transaction_id) VALUES (?,?,?,?,?)",
                              (int(sid), amt, datetime.now().strftime("%Y-%m-%d"), st.session_state['user'], tid))
                    conn.commit()
                    st.info(f"លេខវិក្កយបត្រ: {tid}")
        st.subheader("ប្រវត្តិការបង់ប្រាក់សរុប")
        st.dataframe(pd.read_sql_query("SELECT payments.id, students.name, payments.amount, payments.date, payments.transaction_id FROM payments JOIN students ON payments.student_id = students.id ORDER BY payments.id DESC", conn), use_container_width=True)

    # --- TAB: ATTENDANCE ---
    with tabs[2]:
        st.header("វត្តមានប្រចាំថ្ងៃ")
        today = datetime.now().strftime("%Y-%m-%d")
        for i, row in sts_df.iterrows():
            c1, c2 = st.columns([3, 1])
            c1.write(f"**{row['name']}** ({row['grade']})")
            status = c2.radio("ស្ថានភាព", ["វត្តមាន", "អវត្តមាន"], key=f"att_{row['id']}", horizontal=True)
            if st.button(f"រក្សាទុកវត្តមាន {row['id']}", key=f"btn_att_{row['id']}"):
                c.execute("INSERT INTO attendance (student_id, status, date) VALUES (?,?,?)", (row['id'], status, today))
                conn.commit()
                st.toast("រក្សាទុករួចរាល់!")

    # --- TAB: SKILL PASSPORT ---
    with tabs[3]:
        st.header("📜 Skill Passport & Certification")
        if not sts_df.empty:
            sid_s = st.selectbox("ជ្រើសរើសសិស្ស", sts_df['id'], format_func=lambda x: sts_df[sts_df['id']==x]['name'].values[0], key="s_sid")
            skill = st.text_input("ជំនាញដែលសម្រេចបាន (ឧទាហរណ៍៖ ការវាស់ឈាម)")
            if st.button("បន្ថែមជំនាញ"):
                c.execute("INSERT INTO skill_passport (student_id, skill_name, date_achieved) VALUES (?,?,?)", (sid_s, skill, today))
                conn.commit()
                st.success("ជំនាញត្រូវបានកត់ត្រា!")
        st.subheader("តារាងជំនាញសិស្ស")
        st.table(pd.read_sql_query("SELECT students.name, skill_passport.skill_name, skill_passport.date_achieved FROM skill_passport JOIN students ON skill_passport.student_id = students.id", conn))

    # --- TAB: CURRICULUM ---
    with tabs[4]:
        st.header("🧬 Medical Curriculum Library")
        if role == "Owner":
            with st.expander("បន្ថែមមេរៀនថ្មី"):
                lv = st.selectbox("កម្រិត", ["K1-K4", "P1-P6", "S1-S3", "H1-H3"], key="curr_lv")
                tp = st.text_input("ប្រធានបទ")
                lk = st.text_input("Link ឯកសារ")
                if st.button("រក្សាទុកមេរៀន"):
                    c.execute("INSERT INTO curriculum (level, topic, link) VALUES (?,?,?)", (lv, tp, lk))
                    conn.commit()
        st.dataframe(pd.read_sql_query("SELECT * FROM curriculum", conn), use_container_width=True)

    # --- TAB: HEALTH ---
    with tabs[5]:
        st.header("🍎 Nutrition & Health Tracker")
        if not sts_df.empty:
            sid_h = st.selectbox("ជ្រើសរើសសិស្ស", sts_df['id'], format_func=lambda x: sts_df[sts_df['id']==x]['name'].values[0], key="h_sid")
            h1, h2 = st.columns(2)
            wt = h1.number_input("ទម្ងន់ (kg)", min_value=0.0)
            ht = h2.number_input("កម្ពស់ (cm)", min_value=0.0)
            note = st.text_area("ចំណុចសុខភាព/អាហារូបត្ថម្ភ")
            if st.button("កត់ត្រាសុខភាព"):
                c.execute("INSERT INTO health_tracker (student_id, weight, height, diet_note, date) VALUES (?,?,?,?,?)", (sid_h, wt, ht, note, today))
                conn.commit()
                st.success("កត់ត្រារួចរាល់!")
        st.subheader("របាយការណ៍សុខភាពរួម")
        st.dataframe(pd.read_sql_query("SELECT students.name, health_tracker.weight, health_tracker.height, health_tracker.diet_note, health_tracker.date FROM health_tracker JOIN students ON health_tracker.student_id = students.id", conn), use_container_width=True)

    # --- TAB: INVENTORY ---
    with tabs[6]:
        st.header("🛒 Merchandising & Inventory")
        if role == "Owner":
            with st.expander("គ្រប់គ្រងស្តុក"):
                itm = st.text_input("ឈ្មោះទំនិញ")
                stk = st.number_input("ចំនួន", min_value=0)
                prc = st.number_input("តម្លៃលក់ ($)", min_value=0.0)
                if st.button("រក្សាទុកក្នុងស្តុក"):
                    c.execute("INSERT INTO inventory (item_name, stock, price) VALUES (?,?,?)", (itm, stk, prc))
                    conn.commit()
        st.table(pd.read_sql_query("SELECT * FROM inventory", conn))

    # --- TAB: CEO DASHBOARD ---
    if role == "Owner":
        with tabs[7]:
            st.header("📊 CEO Executive Dashboard")
            col1, col2, col3, col4 = st.columns(4)
            
            total_rev = c.execute("SELECT SUM(amount) FROM payments").fetchone()[0] or 0
            total_st = c.execute("SELECT COUNT(*) FROM students").fetchone()[0]
            total_inv = c.execute("SELECT SUM(stock * price) FROM inventory").fetchone()[0] or 0
            
            col1.metric("ចំណូលសរុប", f"${total_rev:,.2f}")
            col2.metric("សិស្សសរុប", total_st)
            col3.metric("តម្លៃស្តុក", f"${total_inv:,.2f}")
            col4.metric("ស្ថានភាពប្រព័ន្ធ", "Secure")
            
            st.subheader("តារាងត្រួតពិនិត្យវត្តមានថ្ងៃនេះ")
            att_today = pd.read_sql_query(f"SELECT students.name, attendance.status FROM attendance JOIN students ON attendance.student_id = students.id WHERE attendance.date='{today}'", conn)
            st.dataframe(att_today, use_container_width=True)

# --- FOOTER ---
st.markdown(f"<div class='footer'><b>Prepared by CHAN Sokhoeurn, C2/DBA</b> | JMI Enterprise Ecosystem v6.1 | 2026</div>", unsafe_allow_html=True)
