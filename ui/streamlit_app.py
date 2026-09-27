import os
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")
st.set_page_config(page_title="AIA Internal Knowledge Assistant", page_icon="🌍", layout="wide")
st.title("AIA Internal Knowledge Assistant")
st.caption("Bilingual, citation-backed RAG demo")

if "session_id" not in st.session_state:
    st.session_state.session_id = requests.post(f"{API_URL}/sessions", timeout=10).json()["session_id"]
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["text"])

question = st.chat_input("Ask in English or Chinese...")
if question:
    st.session_state.messages.append({"role": "user", "text": question})
    with st.chat_message("user"):
        st.markdown(question)
    response = requests.post(f"{API_URL}/chat", json={"session_id": st.session_state.session_id, "question": question}, timeout=30)
    data = response.json()
    with st.chat_message("assistant"):
        st.markdown(data["answer"])
        if data.get("citations"):
            with st.expander("Sources"):
                for citation in data["citations"]:
                    st.markdown(f"**{citation['id']}** — {citation['document']} (page {citation.get('page')})")
                    st.caption(citation["snippet"])
        st.caption(f"Refused: {data.get('refused')} · Total latency: {data.get('metadata', {}).get('total_ms', 0):.0f} ms")
    st.session_state.messages.append({"role": "assistant", "text": data["answer"]})
