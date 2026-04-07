import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import uuid
import io
import os
from datetime import datetime

# --- 1. DATABASE & TABLES (Updated with Detailed Fees) ---
DATABASE_NAME = 'jmi_enterprise_v7_6.db'
conn = sqlite3.connect(DATABASE_NAME, check_same_thread=False)
c = conn.cursor()

def init_db():
    c.execute('CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, grade TEXT, reg_date TEXT)')
    # Updated Payments table with Fee Type
    c.execute('''CREATE TABLE IF NOT EXISTS payments 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  student_id INTEGER, 
                  fee_type TEXT, 
                  amount REAL, 
                  date TEXT, 
                  staff_name TEXT, 
                  transaction_id TEXT)''')
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)')
    
    # Default Users
    roles = [('ceo_admin', 'JMI@CEO', 'Owner'), ('front_desk', 'JMI@FRONT', 'Front Desk')]
    for u, p, r in roles:
        p_hash = hashlib.sha256(str.encode(p)).hexdigest()
        c.execute("INSERT OR IGNORE INTO users VALUES (?,?,?)", (u, p_hash, r))
    conn.commit()

init_db()

# --- 2. PREMIUM UI STYLING ---
st.set_page_config(page_title="JMI Management Portal", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #000033; }
    h1, h2, h3, label, p, .stMarkdown { color: #D4AF37 !important; }
    .stButton>button { background-color: #D4AF37; color: #000033; font-weight: bold; width: 100%; border-radius: 10px; }
    .stTabs [data-baseweb="tab"] { color: #D4AF37 !important; font-weight: bold; font-size: 16px; }
    .footer { position: fixed; bottom: 0; width: 100%; text-align: center; color: #D4AF37; padding: 10px; background: #00001a; border-top: 1px solid #D4AF37; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. MAIN SYSTEM LOGIC ---
if 'auth' not in st.session_state: st.session_state['auth'] = False

# [Login Logic Omitted for Brevity - Same as v7.5]
# Assuming user is logged in as Owner or Front Desk

if st.session_state.get('auth'):
    role = st.session_state['role']
    st.title(f"🏛️ JMI MASTER SYSTEM - {role} Panel")
    
    # Check if user has access to Enrollment/Finance
    if role in ["Owner", "Front Desk"]:
        tabs = st.tabs(["📝 Enrollment", "💰 Finance & Payments", "🪪 ID Cards", "📊 Finance Reports"])
        
        # TAB 1: ENROLLMENT
        with tabs[0]:
            st.header("Student Registration")
            with st.form("enroll"):
                n = st.text_input("Student Full Name")
                g = st.selectbox("Grade Level", ["K1-K4", "P1-P6", "S1-S3", "H1-H3"])
                if st.form_submit_button("REGISTER STUDENT"):
                    c.execute("INSERT INTO students (name, grade, reg_date) VALUES (?,?,?)", (n, g, datetime.now().strftime("%Y-%m-%d")))
                    conn.commit(); st.success(f"Registered! ID: {c.lastrowid}"); st.rerun()
            
        # TAB 2: FINANCE & PAYMENTS (THE UPDATED SECTION)
        with tabs[1]:
            st.header("Fee Collection Center")
            students_df = pd.read_sql_query("SELECT id, name FROM students", conn)
            
            if not students_df.empty:
                with st.form("payment_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        sid = st.selectbox("Select Student", students_df['id'], format_func=lambda x: students_df[students_df['id']==x]['name'].values[0])
                        # ADDED NEW FEE TYPES
                        ftype = st.selectbox("Fee Category", [
                            "Tuition Fee (ថ្លៃសិក្សា)",
                            "Textbook Fee (ថ្លៃសៀវភៅ)",
                            "Study Kit (ឯកសណ្ឋាន/កាតាប)",
                            "Admin Fee (ថ្លៃរដ្ឋបាល)",
                            "Graduation Fee (ថ្លៃឯកសារបញ្ចប់ការសិក្សា)"
                        ])
                    with col2:
                        amt = st.number_input("Amount ($)", min_value=0.0, step=1.0)
                        date_p = st.date_input("Payment Date", datetime.now())
                    
                    if st.form_submit_button("CONFIRM & PRINT RECEIPT"):
                        tid = str(uuid.uuid4())[:8].upper()
                        c.execute("INSERT INTO payments (student_id, fee_type, amount, date, staff_name, transaction_id) VALUES (?,?,?,?,?,?)", 
                                  (sid, ftype, amt, str(date_p), st.session_state['user'], tid))
                        conn.commit()
                        st.success(f"Payment Successful! Transaction ID: {tid}")

        # TAB 4: FINANCE REPORTS (Owner View)
        with tabs[3]:
            st.header("Revenue Breakdown")
            pay_df = pd.read_sql_query("""
                SELECT p.transaction_id, s.name, p.fee_type, p.amount, p.date 
                FROM payments p 
                JOIN students s ON p.student_id = s.id
            """, conn)
            st.dataframe(pay_df, use_container_width=True)
            
            # Summary by Category
            if not pay_df.empty:
                st.subheader("Summary by Category")
                summary = pay_df.groupby('fee_type')['amount'].sum()
                st.table(summary)

st.markdown(f"<div class='footer'><b>Prepared by Dr. CHAN Sokhoeurn, C2/DBA</b> | JMI v7.6 | 2026</div>", unsafe_allow_html=True)
