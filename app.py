import streamlit as st
import pandas as pd

# --- ការកំណត់សោភ័ណភាព (Theme & Branding) ---
st.set_page_config(page_title="JMI Management System", layout="wide")

# Custom CSS សម្រាប់ពណ៌ Navy Blue និង Gold
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stButton>button { background-color: #000080; color: #FFD700; border-radius: 5px; font-weight: bold; }
    .sidebar .sidebar-content { background-color: #000080; color: white; }
    h1, h2, h3 { color: #000080; }
    .footer { position: fixed; bottom: 10px; width: 100%; text-align: center; font-size: 12px; color: gray; }
    </style>
    """, unsafe_allow_html=True)

# --- Sidebar សម្រាប់បែងចែកសិទ្ធិ (User Roles) ---
st.sidebar.image("https://via.placeholder.com/150x50?text=JMI+LOGO", use_column_width=True)
st.sidebar.title("ប្រព័ន្ធគ្រប់គ្រងសាលា")
role = st.sidebar.selectbox("ជ្រើសរើសតួនាទីបុគ្គលិក (Role)", 
    ["Front Desk (ចុះឈ្មោះ)", "Academic (សិក្សាធិការ)", "HR & Admin", "Owner Dashboard (លោកបណ្ឌិត)"])

st.sidebar.markdown("---")
st.sidebar.write(f"អ្នកកំពុងប្រើប្រាស់ក្នុងនាមជា: **{role}**")

# --- កូដសម្រាប់ផ្នែកនីមួយៗ ---

# ១. ផ្នែក Front Desk (ចុះឈ្មោះ និងលក់)
if role == "Front Desk (ចុះឈ្មោះ)":
    st.header("🏢 ផ្នែកចុះឈ្មោះ និងលក់សម្ភារៈ")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("ចុះឈ្មោះសិស្សថ្មី")
        name = st.text_input("ឈ្មោះសិស្ស")
        grade = st.selectbox("កម្រិតថ្នាក់", ["GEP Level 1", "GEP Level 2", "JMI Foundation"])
        if st.button("រក្សាទុកទិន្នន័យ"):
            st.success(f"បានចុះឈ្មោះ {name} រួចរាល់!")
    with col2:
        st.subheader("លក់សៀវភៅ និងឯកសណ្ឋាន")
        item = st.selectbox("ជ្រើសរើសទំនិញ", ["សៀវភៅ Volume 1", "ឯកសណ្ឋានសាលា (ឈុត)"])
        qty = st.number_input("ចំនួន", min_value=1)
        if st.button("ចេញវិក្កយបត្រ"):
            st.info("វិក្កយបត្រកំពុងដំណើរការ...")

# ២. ផ្នែក Academic (សិក្សាធិការ)
elif role == "Academic (សិក្សាធិការ)":
    st.header("🎓 ផ្នែកសិក្សាធិការ និងការបង្រៀន")
    st.subheader("បញ្ជីឈ្មោះសិស្ស និងពិន្ទុ")
    data = pd.DataFrame({
        'ឈ្មោះសិស្ស': ['សិស្ស ក', 'សិស្ស ខ', 'សិស្ស គ'],
        'ពិន្ទុប្រចាំខែ': [85, 92, 78],
        'អវត្តមាន': [0, 1, 2]
    })
    st.table(data)
    st.text_area("មតិយោបល់គ្រូបង្រៀន")
    st.button("បញ្ជូនរបាយការណ៍")

# ៣. ផ្នែក HR & Admin
elif role == "HR & Admin":
    st.header("👥 ផ្នែកធនធានមនុស្ស និងរដ្ឋបាល")
    st.subheader("វត្តមានបុគ្គលិក និងគ្រូបង្រៀន")
    st.date_input("ជ្រើសរើសថ្ងៃ")
    st.checkbox("គ្រូ វណ្ណា - មកដល់")
    st.checkbox("គ្រូ សុខា - មកដល់")
    st.button("រក្សាទុកវត្តមាន")

# ៤. ផ្នែក Owner Dashboard (លោកបណ្ឌិត)
elif role == "Owner Dashboard (លោកបណ្ឌិត)":
    st.header("📊 ផ្ទាំងគ្រប់គ្រងសម្រាប់លោកបណ្ឌិត (Master View)")
    col1, col2, col3 = st.columns(3)
    col1.metric("សិស្សសរុប", "150 នាក់", "+5%")
    col2.metric("ចំណូលសរុប ($)", "12,500", "+12%")
    col3.metric("ចំណាយសរុប ($)", "4,200", "-2%")
    
    st.subheader("ក្រាហ្វចំណូលប្រចាំខែ")
    chart_data = pd.DataFrame([1000, 2500, 2000, 4500], columns=['Income'])
    st.line_chart(chart_data)

# --- Footer (ឈ្មោះម្ចាស់ប្រព័ន្ធ) ---
st.markdown("""
    <div class="footer">
        Prepared by <b>CHAN Sokhoeurn, C2/DBA</b> | School Management System v1.0
    </div>
    """, unsafe_allow_html=True)
