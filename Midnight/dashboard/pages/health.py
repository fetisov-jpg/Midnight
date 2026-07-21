import streamlit as st
from dashboard.app import fetch

st.set_page_config(page_title="postgres")
st.title("Postgresql")

version = fetch("/postgres/check-version")
if version:
    st.json(version)

processes = fetch("/postgres/requests")
if processes:
    st.subheader("Активные процессы")
    st.dataframe(processes.get("requests", []))