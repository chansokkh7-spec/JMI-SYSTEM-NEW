import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import uuid
import requests
import random
import io
from datetime import datetime

# --- 1. DATABASE & SYSTEM INITIALIZATION ---
conn = sqlite3.connect('jmi_premium_v5_6.db', check_same_thread=False)
c = conn.cursor()

def init_db():
    c.execute('''CREATE TABLE IF NOT EXISTS students 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, grade TEXT, reg_date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS payments 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, amount REAL, 
                  date TEXT, staff_name TEXT, transaction_id TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT, role TEXT)''')
    
    default_users = [
        ('admin', hashlib.sha256(str.encode("JMI@2026")).hexdigest(), 'Owner'),
        ('frontdesk', hashlib.sha256(str.encode("JMI_Staff_FD")).hexdigest(), 'Front Desk')
    ]
    c.executemany("INSERT OR IGNORE INTO users VALUES (?,?,?)", default_users)
    conn.commit()

init_db()

# --- 2. CONFIGURATION ---
def check_hashes(password, hashed_text):
    return hashlib.sha256(str.encode(password)).hexdigest() == hashed_text

# --- 3. PREMIUM NAVY & GOLD UI STYLING ---
st.set_page_config(page_title="JMI Portal | CHAN Sokhoeurn", layout="wide")

st.markdown("""
    <style>
    /* ផ្ទៃ Background ធំ (Navy Blue) */
    .stApp {
        background-color: #000033;
    }
    
    /* Sidebar (Darker Navy) */
    [data-testid="stSidebar"] {
        background-color: #00001a !important;
        border-right: 2px solid #D4AF37;
    }
    
    /* ពណ៌អក្សរទូទៅ (Gold) */
    h1, h2, h3, label, p, .stMarkdown {
        color: #D4AF37 !important;
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #000033;
    }
    .stTabs [data-baseweb="tab"] {
        color: #D4AF37;
    }

    /* Buttons (Gold Background with Navy Text) */
    .stButton>button {
        background-color: #D4AF37;
        color: #000033;
        border: 1px solid #FFD700;
        border-radius: 8px;
        font-weight: bold;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #FFD700;
        color: #000000;
    }

    /* Inputs & Selectboxes */
    input, select, .stSelectbox div {
        background-color: #00004d !important;
        color: #D4AF37 !important;
        border: 1px solid #D4AF37 !important;
    }

    /* Dataframe Styling */
    .stDataFrame {
        border: 1px solid #D4AF37;
    }

    /* Footer Custom */
    .footer {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: #00001a;
        text-align: center;
        padding: 5px;
        font-size: 12px;
        color: #D4AF37;
        border-top: 1px solid #D4AF37;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. AUTHENTICATION ---
if 'auth' not in st.session_state:
    st.session_state['auth'] = False

st.sidebar.markdown("<h2 style='text-align:center;'>JMI ADMIN</h2>", unsafe_allow_html=True)
if not st.session_state['auth']:
    u = st.sidebar.text_input("Username")
    p = st.sidebar.text_input("Password", type='password')
    if st.sidebar.button("LOGIN"):
        res = c.execute("SELECT password, role FROM users WHERE username=?", (u,)).fetchone()
        if res and check_hashes(p, res[0]):
            st.session_state['auth'], st.session_state['user'], st.session_state['role'] = True, u, res[1]
            st.rerun()
        else: st.sidebar.error("Access Denied")
else:
    st.sidebar.write(f"Logged in as: **{st.session_state['user']}**")
    if st.sidebar.button("LOGOUT"):
        st.session_state['auth'] = False
        st.rerun()

# --- 5. FUNCTIONAL MODULES ---
if st.session_state['auth']:
    role = st.session_state['role']

    st.title("🏛️ JMI MANAGEMENT PORTAL")
    
    tab1, tab2, tab3 = st.tabs(["Enrollment", "Payments", "Dashboard"])

    with tab1:
        with st.form("reg_form"):
            st_name = st.text_input("Student Full Name")
            st_level = st.selectbox("Program Path", [
                "K1-K4: Kindergarten", "P1-P6: Primary", 
                "S1-S3: Secondary", "H1-H3: High School", 
                "PUF1-PUF2: Uni Prep"
            ])
            if st.form_submit_button("REGISTER"):
                if st_name:
                    c.execute("INSERT INTO students (name, grade, reg_date) VALUES (?,?,?)", 
                              (st_name, st_level, datetime.now().strftime("%Y-%m-%d")))
                    conn.commit()
                    st.success(f"{st_name} is registered!")

    with tab2:
        st_list = pd.read_sql_query("SELECT id, name FROM students", conn)
        if not st_list.empty:
            sel_id = st.selectbox("Select Student", st_list['id'], format_func=lambda x: st_list[st_list['id']==x]['name'].values[0])
            amt = st.number_input("Amount ($)", min_value=0.0)
            if st.button("COLLECT PAYMENT"):
                tx = str(uuid.uuid4())[:8].upper()
                c.execute("INSERT INTO payments (student_id, amount, date, staff_name, transaction_id) VALUES (?,?,?,?,?)",
                          (int(sel_id), amt, datetime.now().strftime("%Y-%m-%d"), st.session_state['user'], tx))
                conn.commit()
                st.info(f"ID: {tx}")

    with tab3:
        if role == "Owner":
            rev = c.execute("SELECT SUM(amount) FROM payments").fetchone()[0] or 0
            st.metric("Total Revenue", f"${rev:,.2f}")
            st.dataframe(pd.read_sql_query("SELECT * FROM students", conn), use_container_width=True)

st.markdown(f"<div class='footer'><b>Prepared by CHAN Sokhoeurn, C2/DBA</b> | JMI Luxury Ecosystem v5.6</div>", unsafe_allow_html=True)
