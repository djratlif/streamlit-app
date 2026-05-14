import streamlit as st
import time
import os
import requests
import anthropic
import urllib.parse
from google.cloud import firestore

st.set_page_config(page_title="AI Debate Arena", page_icon="⚖️", layout="wide")

# --- Auth & DB Configuration ---
# You can set these in .streamlit/secrets.toml for local testing,
# or in Google Cloud Run environment variables for production.
try:
    GOOGLE_CLIENT_ID = st.secrets.get("GOOGLE_CLIENT_ID", os.environ.get("GOOGLE_CLIENT_ID", ""))
    GOOGLE_CLIENT_SECRET = st.secrets.get("GOOGLE_CLIENT_SECRET", os.environ.get("GOOGLE_CLIENT_SECRET", ""))
    REDIRECT_URI = st.secrets.get("REDIRECT_URI", os.environ.get("REDIRECT_URI", "http://localhost:8501"))
except FileNotFoundError:
    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
    REDIRECT_URI = os.environ.get("REDIRECT_URI", "http://localhost:8501")

def get_login_url():
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "online",
        "prompt": "select_account"
    }
    return "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)

def exchange_code(code):
    data = {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI
    }
    response = requests.post("https://oauth2.googleapis.com/token", data=data)
    if response.status_code == 200:
        return response.json()
    return None

def get_user_info(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get("https://www.googleapis.com/oauth2/v3/userinfo", headers=headers)
    if response.status_code == 200:
        return response.json()
    return None

@st.cache_resource
def get_db():
    return firestore.Client()

def get_user_key(email):
    try:
        db = get_db()
        doc = db.collection("users").document(email).get()
        if doc.exists:
            return doc.to_dict().get("anthropic_api_key", "")
    except Exception as e:
        print(f"Firestore load error: {e}")
    return ""

def save_user_key(email, key):
    try:
        db = get_db()
        db.collection("users").document(email).set({"anthropic_api_key": key}, merge=True)
        return True
    except Exception as e:
        print(f"Firestore save error: {e}")
        return False

# --- State Management ---
if "user" not in st.session_state:
    st.session_state.user = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "debate_active" not in st.session_state:
    st.session_state.debate_active = False
if "debate_finished" not in st.session_state:
    st.session_state.debate_finished = False

# Handle OAuth Callback
query_params = st.query_params
if "code" in query_params and st.session_state.user is None:
    code = query_params["code"]
    tokens = exchange_code(code)
    if tokens and "access_token" in tokens:
        user_info = get_user_info(tokens["access_token"])
        if user_info:
            st.session_state.user = user_info
            
    # Clear query parameters to clean up URL
    st.query_params.clear()

st.title("⚖️ AI Debate Arena")
st.markdown("Watch two AI heavyweights duke it out in real-time over your chosen topic!")

# --- Sidebar ---
st.sidebar.header("Configuration")

# Auth UI
db_api_key = os.environ.get("ANTHROPIC_API_KEY", "")

if st.session_state.user is None:
    if GOOGLE_CLIENT_ID:
        st.sidebar.markdown(
            f'<a href="{get_login_url()}" target="_self"><button style="background-color:#4285F4;color:white;border:none;padding:10px;border-radius:5px;cursor:pointer;width:100%;margin-bottom:15px;font-weight:bold;">Sign in with Google</button></a>', 
            unsafe_allow_html=True
        )
        st.sidebar.caption("Sign in to securely save your API key to your account.")
    else:
        st.sidebar.warning("Google Login is not configured yet.")
    st.sidebar.divider()
else:
    user = st.session_state.user
    st.sidebar.markdown(f"👤 Logged in as **{user.get('email')}**")
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.rerun()
    
    # Try fetching the key from Firestore
    fetched_key = get_user_key(user.get('email'))
    if fetched_key:
        db_api_key = fetched_key
        
    st.sidebar.divider()

# Input box for API Key
anthropic_api_key_input = st.sidebar.text_input(
    "Anthropic API Key (for all agents)", 
    type="password", 
    value=db_api_key
)
anthropic_api_key = anthropic_api_key_input.strip()

# Save Key Button (Only if logged in)
if st.session_state.user is not None:
    if st.sidebar.button("Save Key to Account"):
        if anthropic_api_key:
            if save_user_key(st.session_state.user.get('email'), anthropic_api_key):
                st.sidebar.success("Key saved securely to your account!")
            else:
                st.sidebar.error("Failed to save key. Check database permissions.")
        else:
            st.sidebar.warning("Please enter a key first.")

topic = st.sidebar.text_area("Debate Topic", "Is a hot dog a sandwich?")
start_button = st.sidebar.button("Start Debate")


def render_messages():
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar=msg.get("avatar", None)):
            st.markdown(f"**{msg['name']}**: {msg['content']}")

render_messages()

# --- Debate Logic ---
MAX_TURNS = 5

def generate_calvin_response(topic, history):
    client = anthropic.Anthropic(api_key=anthropic_api_key)
    
    messages = []
    messages.append({"role": "user", "content": "Please start the debate."})
    
    for msg in history:
        if msg["name"] == "Calvin":
            messages.append({"role": "assistant", "content": msg["content"]})
        elif msg["name"] == "Chester":
            messages.append({"role": "user", "content": f"Chester says: {msg['content']}"})
            
    system_prompt = (
        "You are Calvin, a sharp, witty debater. You are debating Chester. "
        f"The topic of the debate is: {topic}. "
        "Keep your responses concise (under 150 words). Focus on strong logical points, "
        "rebutting Chester when necessary, and making a persuasive case. "
        f"You have {MAX_TURNS} turns total."
    )
    
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        system=system_prompt,
        messages=messages
    )
    return response.content[0].text

def generate_chester_response(topic, history):
    client = anthropic.Anthropic(api_key=anthropic_api_key)
    
    messages = []
    
    for msg in history:
        if msg["name"] == "Chester":
            messages.append({"role": "assistant", "content": msg["content"]})
        elif msg["name"] == "Calvin":
            messages.append({"role": "user", "content": f"Calvin says: {msg['content']}"})
            
    system_prompt = (
        "You are Chester, a sharp, witty debater. You are debating Calvin. "
        f"The topic of the debate is: {topic}. "
        "Keep your responses concise (under 150 words). Focus on strong logical points, "
        "rebutting Calvin when necessary, and making a persuasive case. "
        f"You have {MAX_TURNS} turns total."
    )
        
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        system=system_prompt,
        messages=messages
    )
    return response.content[0].text

def generate_judge_verdict(topic, history):
    client = anthropic.Anthropic(api_key=anthropic_api_key)
    
    transcript = ""
    for i, msg in enumerate(history):
        transcript += f"[{msg['name']}]: {msg['content']}\n\n"
        
    prompt = (
        f"You are an impartial, highly analytical judge. The topic of the debate was: '{topic}'.\n\n"
        f"Here is the transcript of the debate between Calvin and Chester:\n\n{transcript}\n\n"
        "Please analyze the debate. Evaluate their arguments, persuasiveness, conciseness, and rebuttals. "
        "CRITICAL INSTRUCTION: You MUST explicitly declare a single winner. You are not allowed to call it a tie. "
        "Conclude your analysis with a clear, prominent declaration of the winner formatted exactly like this: \n\n"
        "### 🏆 WINNER: [Calvin or Chester]"
    )
    
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=800,
        system="You are the final judge of an AI debate. Provide a clear, detailed ruling.",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return response.content[0].text

if start_button:
    if not anthropic_api_key:
        st.error("Please provide an Anthropic API key in the sidebar.")
    elif not topic:
        st.error("Please provide a debate topic.")
    else:
        st.session_state.messages = []
        st.session_state.debate_active = True
        st.session_state.debate_finished = False
        st.rerun()

if st.session_state.debate_active and not st.session_state.debate_finished:
    history = st.session_state.messages
    turn_count = len(history) // 2
    
    if len(history) < MAX_TURNS * 2:
        # Calvin's turn
        if len(history) % 2 == 0:
            with st.spinner("Calvin is thinking..."):
                try:
                    calvin_text = generate_calvin_response(topic, history)
                    st.session_state.messages.append({"name": "Calvin", "role": "assistant", "avatar": "🦤", "content": calvin_text})
                    st.rerun()
                except Exception as e:
                    st.error(f"Error calling Anthropic API: {e}")
                    st.session_state.debate_active = False
            
        # Chester's turn
        else:
            with st.spinner("Chester is thinking..."):
                try:
                    chester_text = generate_chester_response(topic, history)
                    st.session_state.messages.append({"name": "Chester", "role": "assistant", "avatar": "🤖", "content": chester_text})
                    st.rerun()
                except Exception as e:
                    st.error(f"Error calling Anthropic API: {e}")
                    st.session_state.debate_active = False
    else:
        st.session_state.debate_finished = True
        st.rerun()

if st.session_state.debate_finished:
    st.markdown("---")
    st.subheader("⚖️ The Judge's Verdict")
    with st.spinner("The Judge is deliberating..."):
        try:
            verdict = generate_judge_verdict(topic, st.session_state.messages)
            with st.chat_message("assistant", avatar="⚖️"):
                st.markdown("**The Judge**: " + verdict)
        except Exception as e:
            st.error(f"Error calling Anthropic API for Judge: {e}")
    
    if st.button("Reset Debate"):
        st.session_state.messages = []
        st.session_state.debate_active = False
        st.session_state.debate_finished = False
        st.rerun()