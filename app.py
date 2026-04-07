import io

# --- មុខងារទាញយកទិន្នន័យសម្រាប់ថ្នាក់ដឹកនាំ (CEO/Founder/Board) ---
if role == "Owner (របាយការណ៍មេ)":
    st.header("📥 មជ្ឈមណ្ឌលទាញយកទិន្នន័យ (Admin Export)")
    
    # បង្កើត Tab សម្រាប់បែងចែករបាយការណ៍
    tab_data, tab_logs = st.tabs(["ទិន្នន័យសិស្ស & ហិរញ្ញវត្ថុ", "ដានសកម្មភាពបុគ្គលិក"])
    
    with tab_data:
        # ទាញទិន្នន័យរួមបញ្ចូលគ្នារវាង សិស្ស និង ការបង់ប្រាក់
        query = """
        SELECT s.name, s.grade, p.amount, p.date, p.transaction_id, p.staff_name 
        FROM students s 
        LEFT JOIN payments p ON s.id = p.student_id
        """
        full_df = pd.read_sql_query(query, conn)
        st.dataframe(full_df)

        # បំប្លែងទិន្នន័យទៅជា Excel ក្នុង Memory (មិនរក្សាទុកក្នុង Server នាំឱ្យលេចធ្លាយ)
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            full_df.to_excel(writer, index=False, sheet_name='Full_Report')
        
        # ប៊ូតុងទាញយក (មានតែក្នុង Module Owner នេះទេទើបឃើញ)
        st.download_button(
            label="ទាញយកទិន្នន័យទាំងមូលជា Excel (CEO Only)",
            data=buffer,
            file_name=f"JMI_Full_Report_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
            mime="application/vnd.ms-excel"
        )

    with tab_logs:
        st.subheader("📝 ពិនិត្យដានសកម្មភាព (Audit Logs)")
        log_df = pd.read_sql_query("SELECT * FROM activity_logs ORDER BY id DESC", conn)
        st.table(log_df)
