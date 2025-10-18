# frontend/views/admin/api_management_view.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone
from backend.db.db_handler import get_session, get_api_logs_last_n_days
from backend.llm_client import test_api_provider

def render_api_management_view():
    st.title("📈 API & Model Management")
    st.markdown("---")

    # --- 1. API Status Tester ---
    st.header("Provider Status")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Test Gemini API"):
            with st.spinner("Testing Gemini..."):
                success, message = test_api_provider("gemini")
                if success:
                    st.success(message)
                else:
                    st.error(message)
    with col2:
        if st.button("Test Ollama (llama2) API"):
            with st.spinner("Testing Ollama..."):
                success, message = test_api_provider("ollama", model="llama2")
                if success:
                    st.success(message)
                else:
                    st.error(message)
    
    st.markdown("---")

    # --- 2. API Usage Analytics ---
    st.header("API Call Analytics (Last 30 Days)")
    
    try:
        with get_session() as db:
            logs = get_api_logs_last_n_days(db, days=30)
        
        if not logs:
            st.info("No API calls have been logged in the last 30 days.")
            return # Use return instead of st.stop()

        log_data = [{
            "provider": log.provider,
            "model": log.model,
            "date": log.created_at.date() # Extracting date is fine here
        } for log in logs]
        df = pd.DataFrame(log_data)

        # --- 2a. KPI Metrics ---
        now_utc = datetime.now(timezone.utc)
        logs_24h = [log for log in logs if log.created_at >= (now_utc - timedelta(days=1))]
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Calls (30d)", value=len(df))
        col2.metric("Total Calls (24h)", value=len(logs_24h))
        
        gemini_calls_30d = len(df[df['provider'] == 'Gemini'])
        col3.metric("Gemini Calls (30d)", value=gemini_calls_30d)

        # --- 2b. Usage Charts ---
        st.subheader("Calls per Day")
        calls_per_day = df.groupby('date').size().reset_index(name='Total Calls')
        calls_per_day = calls_per_day.set_index('date')
        st.bar_chart(calls_per_day)

        st.subheader("Calls by Provider")
        calls_by_provider = df.groupby('provider').size().reset_index(name='Total Calls')
        st.bar_chart(calls_by_provider.set_index('provider')) 

    except Exception as e:
        st.error(f"An error occurred while generating analytics: {e}")