import os
import datetime
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")

st.set_page_config(page_title="Multi-Context Research Assistant", page_icon="🔬", layout="centered")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "processing" not in st.session_state:
    st.session_state.processing = False

st.markdown(
    f"""
    <style>
    div[data-testid="stChatInput"] {{
        padding-bottom: 0.3rem !important;
    }}
    
    div[data-testid="stChatInput"]::after {{
        content: "Copyright © {datetime.date.today().year} Anand Shenoy. All Rights Reserved.";
        display: block;
        width: 100%;
        text-align: center;
        color: gray;
        font-size: 0.8em;
        margin-top: 15px;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <style>
    div[data-testid="stElementContainer"]:has(.sticky-header-wrapper) {
        position: sticky;
        top: 2.875rem; 
        z-index: 999;
        background-color: white !important;
    }
    
    .sticky-header-wrapper {
        background-color: white;
        padding-top: 15px;
        padding-bottom: 15px;
        border-bottom: 1px solid #e6e6e6;
        margin-bottom: 0;
        width: 97%;
    }
    
    h1.main-title {
        margin-bottom: 0 !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }
    </style>
    
    <div class="sticky-header-wrapper">
        <h2 class="main-title" style="text-align: center;"><big><b> Multi-Context Research Assistant</b></big></h2>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

for message in st.session_state.messages:
    avatar = "🧑‍💻" if message["role"] == "user" else "🤖"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask a question about the research...", disabled=st.session_state.processing):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.processing = True
    st.rerun()

if st.session_state.processing and st.session_state.messages:
    last_message = st.session_state.messages[-1]

    if last_message["role"] == "user":
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Thinking... 💭"):
                try:
                    response = requests.post(
                        N8N_WEBHOOK_URL,
                        json={"chatInput": last_message["content"]},
                        timeout=60,
                    )
                    response.raise_for_status()

                    try:
                        data = response.json()
                    except ValueError:
                        data = {"output": response.text}

                    if isinstance(data, list):
                        data = data

                    raw_output = (
                        data.get("output")
                        or data.get("text")
                        or data.get("message")
                        or data.get("response")
                        or str(data)
                    )

                    if isinstance(raw_output, list):
                        clean_text = "".join([
                            item["text"] if isinstance(item, dict) and "text" in item else str(item)
                            for item in raw_output
                        ])
                    else:
                        clean_text = str(raw_output)

                    st.markdown(clean_text)
                    st.session_state.messages.append({"role": "assistant", "content": clean_text})

                except requests.exceptions.Timeout:
                    clean_text = "⚠️ The request timed out. The n8n workflow took too long to respond."
                    st.error(clean_text)
                    st.session_state.messages.append({"role": "assistant", "content": clean_text})

                except requests.exceptions.ConnectionError:
                    clean_text = "⚠️ Could not connect to the n8n workflow. Please check that your webhook URL is correct and n8n is running."
                    st.error(clean_text)
                    st.session_state.messages.append({"role": "assistant", "content": clean_text})

                except Exception as e:
                    clean_text = f"⚠️ Unexpected error: {e}"
                    st.error(clean_text)
                    st.session_state.messages.append({"role": "assistant", "content": clean_text})

                finally:
                    st.session_state.processing = False
                    st.rerun()