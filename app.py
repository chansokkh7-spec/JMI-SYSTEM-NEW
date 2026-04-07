import requests
import random

# --- កូដផ្ញើទៅ Telegram (ដាក់នៅផ្នែកខាងលើនៃ Script) ---
def send_telegram_otp(otp_code):
    token = "លេខ_TOKEN_របស់_BOT" # លោកបណ្ឌិតត្រូវបង្កើត Bot ក្នុង Telegram
    chat_id = "លេខ_ID_របស់_លោកបណ្ឌិត" # លេខ ID Telegram ផ្ទាល់ខ្លួន
    message = f"🔐 កូដផ្ទៀងផ្ទាត់សម្រាប់ទាញយកទិន្នន័យ JMI គឺ៖ {otp_code}"
    url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={message}"
    requests.get(url)

# --- ក្នុងផ្នែក Owner Dashboard ---
if role == "Owner (របាយការណ៍មេ)":
    st.header("📥 មជ្ឈមណ្ឌលទាញយកទិន្នន័យ (CEO Only)")

    # ១. បង្កើតស្ថានភាពសម្រាប់ OTP (Session State)
    if 'otp_sent' not in st.session_state:
        st.session_state.otp_sent = False
    if 'generated_otp' not in st.session_state:
        st.session_state.generated_otp = None

    # ២. ប៊ូតុងផ្ញើកូដ
    if st.button("ផ្ញើកូដផ្ទៀងផ្ទាត់ទៅ Telegram"):
        otp = random.randint(100000, 999999)
        st.session_state.generated_otp = str(otp)
        send_telegram_otp(otp)
        st.session_state.otp_sent = True
        st.info("កូដត្រូវបានផ្ញើទៅ Telegram របស់លោកបណ្ឌិតហើយ!")

    # ៣. ប្រអប់ផ្ទៀងផ្ទាត់កូដ
    if st.session_state.otp_sent:
        user_otp = st.text_input("បញ្ចូលកូដ ៦ ខ្ទង់ពី Telegram", type="password")
        
        if user_otp == st.session_state.generated_otp:
            st.success("ការផ្ទៀងផ្ទាត់ជោគជ័យ! លោកបណ្ឌិតអាចទាញយកទិន្នន័យបានឥឡូវនេះ។")
            
            # --- ប៊ូតុង Download Excel (ដាក់ក្នុងលក្ខខណ្ឌបើកូដត្រូវ) ---
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                full_df.to_excel(writer, index=False)
            
            st.download_button(
                label="📥 ចុចទីនេះដើម្បីទាញយក Excel",
                data=buffer,
                file_name="JMI_Secure_Report.xlsx",
                mime="application/vnd.ms-excel"
            )
        elif user_otp != "":
            st.error("កូដមិនត្រឹមត្រូវទេ សូមពិនិត្យម្ដងទៀត!")
