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
conn = sqlite3.connect('jmi_premium_v5_5.db', check_same_thread=False)
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
TELEGRAM_TOKEN = "YOUR_BOT_TOKEN_HERE"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID_HERE"

def check_hashes(password, hashed_text):
    return hashlib.sha256(str.encode(password)).hexdigest() == hashed_text

# --- 3. PREMIUM NAVY & GOLD UI STYLING ---
st.set_page_config(page_title="JMI Portal | CHAN Sokhoeurn", layout="wide")

st.markdown("""
    <style>
    /* ផ្ទៃខាងក្រោយកម្មវិធីទាំងមូល (Navy Blue) */
    .stApp {
        background-color: #000033;
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #000022;
        border-right: 3px solid #D4AF37; /* Gold Border */
    }
    
    /* ការកំណត់ពណ៌អក្សរទូទៅឱ្យទៅជាពណ៌មាស ឬស */
    h1, h2, h3, p, span, label, .stMarkdown {
        color: #D4AF37 !important; /* Gold Color */
    }
    
    /* ប៊ូតុង Styling (Gold Background with Navy Text) */
    .stButton>button {
        background-color: #D4AF37;
        color: #000033;
        border: 2px solid #B8860B;
        border-radius: 12px;
        font-weight: bold;
        font-size: 18px;
        transition: 0.3s;
    }
    
    .stButton>button:hover {
        background-color: #FFD700;
        color: #000000;
        border: 2px solid #FFFFFF;
    }

    /* Input Fields Styling */
    .stTextInput>div>div>input, .stSelectbox>div>div>div {
        background-color: #000055;
        color: #D4AF37 !important;
        border: 1px solid #D4AF37;
    }

    /* Footer Styling */
    .footer {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: #000022;
        text-align: center;
        padding: 10px;
        font-size: 14px;
        color: #D4AF37;
        border-top: 2px solid #D4AF37;
        z-index: 100;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. AUTHENTICATION ---
if 'auth' not in st.session_state:
    st.session_state['auth'] = False

st.sidebar.markdown("<h1 style='text-align:center; color:#D4AF37;'>JMI</h1>", unsafe_allow_html=True)
if not st.session_state['auth']:
    u = st.sidebar.text_input("Username")
    p = st.sidebar.text_input("Password", type='password')
    if st.sidebar.button("LOGIN TO JMI"):
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

    if role in ["Owner", "Front Desk"]:
        st.title("🏛️ JMI Enrollment System")
        col_reg, col_pay = st.columns(2)
        
        with col_reg:
            with st.form("enroll_form"):
                st.subheader("📝 New Registration")
                st_name = st.text_input("Student Name")
                program_options = [
                    "K1-K4: JMI Kindergarten",
                    "P1-P6: JMI Primary",
                    "S1-S3: JMI Secondary",
                    "H1-H3: JMI High School",
                    "PUF1-PUF2: JMI University Prep"
                ]
                st_level = st.selectbox("Program Path", program_options)
                if st.form_submit_button("REGISTER NOW"):
                    if st_name:
                        c.execute("INSERT INTO students (name, grade, reg_date) VALUES (?,?,?)", 
                                  (st_name, st_level, datetime.now().strftime("%Y-%m-%d")))
                        conn.commit()
                        st.success(f"Success! {st_name} joined {st_level}")

        with col_pay:
            st.subheader("💰 Payment Collection")
            st_list = pd.read_sql_query("SELECT id, name FROM students", conn)
            if not st_list.empty:
                sel_id = st.selectbox("Select Student", st_list['id'], format_func=lambda x: st_list[st_list['id']==x]['name'].values[0])
                amt = st.number_input("Amount ($)", min_value=0.0)
                if st.button("ISSUE RECEIPT"):
                    tx = str(uuid.uuid4())[:8].upper()
                    c.execute("INSERT INTO payments (student_id, amount, date, staff_name, transaction_id) VALUES (?,?,?,?,?)",
                              (int(sel_id), amt, datetime.now().strftime("%Y-%m-%d %H:%M"), st.session_state['user'], tx))
                    conn.commit()
                    st.info(f"Transaction ID: {tx}")

    if role == "Owner":
        st.markdown("---")
        st.title("📊 CEO Dashboard")
        rev = c.execute("SELECT SUM(amount) FROM payments").fetchone()[0] or 0
        st.metric("Total Revenue", f"${rev:,.2f}")
        
        st.subheader("📋 Student Master List")
        all_st = pd.read_sql_query("SELECT * FROM students", conn)
        st.dataframe(all_st, use_container_width=True)

# --- 6. FOOTER ---
st.markdown(f"<div class='footer'><b>Prepared by CHAN Sokhoeurn, C2/DBA</b> | Junior Medical Institute | Luxury Portal v5.5</div>", unsafe_allow_html=True)
