import requests
import streamlit as st

API = st.sidebar.text_input("Local API", "http://127.0.0.1:8000")
st.title("AegisSOC-X — Analyst Console")
st.caption("Portfolio prototype: localhost only. No authentication or production safeguards.")

try:
    health = requests.get(f"{API}/health", timeout=5).json()
    cases = requests.get(f"{API}/cases", timeout=5).json()
    audit = requests.get(f"{API}/audit", timeout=5).json()
except requests.RequestException:
    st.error("Start the API: uv run uvicorn aegissoc.api:app --reload")
    st.stop()

col1, col2, col3 = st.columns(3)
col1.metric("Model ready", "Yes" if health["model_ready"] else "No")
col2.metric("Recent cases", len(cases))
col3.metric("Recent audit events", len(audit))

st.subheader("Investigation queue")
st.dataframe(cases, use_container_width=True)
st.subheader("Review a case")
case_id = st.number_input("Case ID", min_value=1, step=1)
if st.button("Investigate"):
    r = requests.post(f"{API}/cases/{case_id}/investigate", timeout=65)
    st.json(r.json())
reviewer = st.text_input("Reviewer (demo label)")
decision = st.selectbox("Decision", ["benign", "confirmed", "needs_more_evidence"])
if st.button("Submit review"):
    r = requests.post(
        f"{API}/cases/{case_id}/review",
        json={"reviewer": reviewer, "decision": decision},
        timeout=10,
    )
    st.json(r.json())
st.subheader("Audit trail")
st.dataframe(audit, use_container_width=True)
