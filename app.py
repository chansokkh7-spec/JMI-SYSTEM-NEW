import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import uuid
from datetime import datetime

# --- 1. DATABASE SETUP ---
DATABASE_NAME = 'jmi_final_v6_2.db'
conn = sqlite3.connect(DATABASE_NAME, check_same_thread=False)
c = conn.cursor()

def init_db():
    c.execute('CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, grade TEXT, reg_date TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, amount REAL, date TEXT, staff_name TEXT, transaction_id TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS attendance (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, status TEXT, date TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS skill_passport (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, skill_name TEXT, date_achieved TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS health_tracker (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, weight REAL, height REAL, diet_note TEXT, date TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS curriculum (id INTEGER PRIMARY KEY AUTOINCREMENT, level TEXT, topic TEXT, link TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS inventory (id INTEGER PRIMARY KEY AUTOINCREMENT, item_name TEXT, stock INTEGER, price REAL)')
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)')
    
    admin_hash = hashlib.sha256(str.encode("JMI@2026")).hexdigest()
    c.execute("INSERT OR IGNORE INTO users VALUES (?,?,?)", ('admin', admin_hash, 'Owner'))
    conn.commit()

init_db()

# --- 2. THEME & STYLE ---
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

# --- 3. AUTHENTICATION ---
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
    st.title("🏛️ JMI MASTER SYSTEM v6.2")
    
    menu = ["📝 Enrollment", "💰 Payments", "📅 Attendance", "📜 Skill Passport", "🧬 Curriculum", "🍎 Health", "🛒 Inventory", "👤 Profile Search"]
    if role == "Owner": menu.append("📊 CEO Dashboard")
    tabs = st.tabs(menu)

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
        st.dataframe(pd.read_sql_query("SELECT * FROM students ORDER BY id DESC LIMIT 5", conn), use_container_width=True)

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
        st.subheader("ប្រវត្តិការបង់ប្រាក់ចុងក្រោយ")
        st.dataframe(pd.read_sql_query("SELECT payments.id, students.name, payments.amount, payments.date FROM payments JOIN students ON payments.student_id = students.id ORDER BY payments.id DESC LIMIT 10", conn), use_container_width=True)

    # --- TAB: ATTENDANCE (Teacher Mode Optimized) ---
    with tabs[2]:
        st.header("វត្តមានប្រចាំថ្ងៃ (Teacher Mode)")
        today = datetime.now().strftime("%Y-%m-%d")
        
        # មុខងារ Filter តាមថ្នាក់សម្រាប់គ្រូ
        f_grade = st.selectbox("ជ្រើសរើសថ្នាក់ដែលត្រូវចុះវត្តមាន", ["All Grades", "K1-K4", "P1-P6", "S1-S3", "H1-H3", "PUF1-PUF2"])
        
        if f_grade != "All Grades":
            filtered_sts = sts_df[sts_df['grade'] == f_grade]
        else:
            filtered_sts = sts_df

        if not filtered_sts.empty:
            for i, row in filtered_sts.iterrows():
                c1, c2 = st.columns([3, 1])
                c1.write(f"**{row['name']}**")
                status = c2.radio("ស្ថានភាព", ["វត្តមាន", "អវត្តមាន"], key=f"att_{row['id']}", horizontal=True)
                if st.button(f"រក្សាទុកវត្តមាន {row['name']}", key=f"btn_att_{row['id']}"):
                    c.execute("INSERT INTO attendance (student_id, status, date) VALUES (?,?,?)", (row['id'], status, today))
                    conn.commit()
                    st.toast(f"បានរក្សាទុកវត្តមានសម្រាប់ {row['name']}")
        else:
            st.warning("មិនមានសិស្សក្នុងថ្នាក់នេះទេ។")

    # --- TAB: SKILL PASSPORT ---
    with tabs[3]:
        st.header("📜 Skill Passport")
        if not sts_df.empty:
            sid_s = st.selectbox("ជ្រើសរើសសិស្ស", sts_df['id'], format_func=lambda x: sts_df[sts_df['id']==x]['name'].values[0], key="s_sid")
            skill = st.text_input("ជំនាញដែលសម្រេចបាន")
            if st.button("បន្ថែមជំនាញ"):
                c.execute("INSERT INTO skill_passport (student_id, skill_name, date_achieved) VALUES (?,?,?)", (sid_s, skill, today))
                conn.commit()
                st.success("ជំនាញត្រូវបានកត់ត្រា!")
        st.table(pd.read_sql_query("SELECT students.name, skill_passport.skill_name, skill_passport.date_achieved FROM skill_passport JOIN students ON skill_passport.student_id = students.id ORDER BY skill_passport.id DESC LIMIT 10", conn))

    # --- TAB: CURRICULUM ---
    with tabs[4]:
        st.header("🧬 Medical Curriculum")
        if role == "Owner":
            with st.expander("បន្ថែមមេរៀន"):
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
            note = st.text_area("ចំណុចសុខភាព")
            if st.button("កត់ត្រាសុខភាព"):
                c.execute("INSERT INTO health_tracker (student_id, weight, height, diet_note, date) VALUES (?,?,?,?,?)", (sid_h, wt, ht, note, today))
                conn.commit()
                st.success("កត់ត្រារួចរាល់!")

    # --- TAB: INVENTORY ---
    with tabs[6]:
        st.header("🛒 Inventory")
        if role == "Owner":
            with st.expander("គ្រប់គ្រងស្តុក"):
                itm = st.text_input("ឈ្មោះទំនិញ")
                stk = st.number_input("ចំនួន", min_value=0)
                prc = st.number_input("តម្លៃ ($)", min_value=0.0)
                if st.button("រក្សាទុក"):
                    c.execute("INSERT INTO inventory (item_name, stock, price) VALUES (?,?,?)", (itm, stk, prc))
                    conn.commit()
        st.table(pd.read_sql_query("SELECT * FROM inventory", conn))

    # --- TAB: PROFILE SEARCH (NEW FEATURE) ---
    with tabs[7]:
        st.header("👤 សាវតាសិស្សលម្អិត (Student Profile)")
        if not sts_df.empty:
            search_id = st.selectbox("ស្វែងរកឈ្មោះសិស្ស", sts_df['id'], format_func=lambda x: sts_df[sts_df['id']==x]['name'].values[0])
            
            p1, p2, p3 = st.columns(3)
            # បង្ហាញជំនាញ
            p1.subheader("📜 ជំនាញសម្រេចបាន")
            p1.dataframe(pd.read_sql_query(f"SELECT skill_name, date_achieved FROM skill_passport WHERE student_id={search_id}", conn))
            
            # បង្ហាញសុខភាព
            p2.subheader("🍎 សន្ទស្សន៍សុខភាព")
            p2.dataframe(pd.read_sql_query(f"SELECT weight, height, date FROM health_tracker WHERE student_id={search_id}", conn))
            
            # បង្ហាញការបង់ប្រាក់
            p3.subheader("💰 ប្រវត្តការបង់ប្រាក់")
            p3.dataframe(pd.read_sql_query(f"SELECT amount, date FROM payments WHERE student_id={search_id}", conn))

    # --- TAB: CEO DASHBOARD ---
    if role == "Owner":
        with tabs[8]:
            st.header("📊 CEO Dashboard")
            col1, col2, col3 = st.columns(3)
            col1.metric("ចំណូលសរុប", f"${c.execute('SELECT SUM(amount) FROM payments').fetchone()[0] or 0:,.2f}")
            col2.metric("សិស្សសរុប", len(sts_df))
            col3.metric("តម្លៃស្តុក", f"${c.execute('SELECT SUM(stock * price) FROM inventory').fetchone()[0] or 0:,.2f}")

st.markdown(f"<div class='footer'><b>Prepared by CHAN Sokhoeurn, C2/DBA</b> | JMI v6.2 | 2026</div>", unsafe_allow_html=True)
