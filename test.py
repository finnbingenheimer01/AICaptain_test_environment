import streamlit as st
import requests

# --- CONFIGURATION ---
BASE_URL = "https://dev-ai-captain.aws.cloud.roche.com"
API_KEY = "AOesgf37PoOYNpL8hYDBKOc04TQb5BJg" 

# --- UI CONFIG ---
st.set_page_config(page_title="Roche AI Captain", page_icon="🧬", layout="wide")

# Custom CSS for the "Roche Look"
st.markdown("""
    <style>
    .main {
        background-color: #f5f7f9;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #0066CC;
        color: white;
    }
    .stSidebar {
        background-color: #ffffff;
        border-right: 1px solid #e6e9ef;
    }
    div[data-testid="stExpander"] {
        border: none !important;
        box-shadow: none !important;
        background-color: transparent !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- SESSION STATE ---
if "conv_id" not in st.session_state:
    st.session_state.conv_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- API FUNCTIONS ---
def initiate_session():
    headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
    
    # Step 1: Initiate session
    payload_init = {"browser_session_id": "streamlit_user_001"}
    res_init = requests.post(f"{BASE_URL}/api/v1/sessions/initiate", json=payload_init, headers=headers)
    data_init = res_init.json()
    
    if data_init.get("success"):
        flow = data_init["data"].get("flow")
        
        # If flow is "tnc", we must accept terms and conditions
        if flow == "tnc":
            payload_ack = {
                "browser_session_id": "streamlit_user_001",
                "acknowledged": True
            }
            # Step 2: Acknowledge 
            res_ack = requests.post(f"{BASE_URL}/api/v1/sessions/acknowledge", json=payload_ack, headers=headers)
            data_ack = res_ack.json()
            
            if data_ack.get("success"):
                # Now we receive the actual conversation_id
                st.session_state.conv_id = data_ack["data"].get("conversation_id")
                return st.session_state.conv_id
        
        # If flow is "init" or "history", the ID is already present
        elif data_init["data"].get("conversation_id"):
            st.session_state.conv_id = data_init["data"].get("conversation_id")
            return st.session_state.conv_id

    st.error("Error initializing the session.")
    return None

def send_message(query):
    headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
    payload = {"conversation_id": str(st.session_state.conv_id), "query": query}
    url = f"{BASE_URL.rstrip('/')}/api/v1/messages"
    res = requests.post(url, json=payload, headers=headers)
    return res.json()

def submit_feedback(rating, comment):
    headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
    payload = {
        "conversation_id": str(st.session_state.conv_id),
        "rating": float(rating),
        "comment": comment
    }
    url = f"{BASE_URL.rstrip('/')}/api/v1/conversations/feedback"
    res = requests.post(url, json=payload, headers=headers)
    return res.json()

# --- SIDEBAR ---
with st.sidebar:
    st.title("Settings")
    
    with st.expander("Session Info", expanded=True):
        st.caption("Active Conversation ID:")
        st.code(st.session_state.conv_id if st.session_state.conv_id else "Not started")

    if st.button("🗑️ Clear Chat"):
        st.session_state.conv_id = None
        st.session_state.messages = []
        st.rerun()

# --- MAIN UI ---
st.title("🧬 Roche AI Captain")
st.markdown("Ask me for details about **cobas®** systems, reagents, or technical specifications.")

# Auto-init
if st.session_state.conv_id is None:
    initiate_session()

# Chat Container
chat_container = st.container()

with chat_container:
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            # Feedback only for assistant messages
            if msg["role"] == "assistant":
                col1, col2 = st.columns([1, 4])
                with col1:
                    if st.button("👍", key=f"up_{i}"):
                        submit_feedback(5.0, "Easy like")
                        st.toast("Thanks for your feedback!")

# User Input
if prompt := st.chat_input("Enter your question here..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with chat_container:
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Roche AI is thinking..."):
                response = send_message(prompt)
                
            if response.get("success"):
                answer = response["data"]["content"]
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
                
                # Subtle feedback form at the end
                with st.expander("Rate this response"):
                    f_col1, f_col2 = st.columns([2,1])
                    rating = f_col1.slider("Stars", 1.0, 5.0, 5.0, 0.5, key=f"slide_{len(st.session_state.messages)}")
                    comment = f_col1.text_input("Comment (optional)", key=f"comm_{len(st.session_state.messages)}")
                    if f_col2.button("Submit", key=f"btn_{len(st.session_state.messages)}"):
                        submit_feedback(rating, comment)
                        st.success("Feedback saved!")
            else:
                st.error(f"API Error: {response.get('detail', 'Unknown error')}")
