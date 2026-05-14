import streamlit as st
import time
import os
import anthropic

st.set_page_config(page_title="AI Debate Arena", page_icon="⚖️", layout="wide")

st.title("⚖️ AI Debate Arena")
st.markdown("Watch two AI heavyweights duke it out in real-time over your chosen topic!")

# --- Sidebar ---
st.sidebar.header("Configuration")
anthropic_api_key_input = st.sidebar.text_input("Anthropic API Key (for all agents)", type="password", value=os.environ.get("ANTHROPIC_API_KEY", ""))
anthropic_api_key = anthropic_api_key_input.strip()
topic = st.sidebar.text_area("Debate Topic", "Is a hot dog a sandwich?")
start_button = st.sidebar.button("Start Debate")

# --- State Management ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "debate_active" not in st.session_state:
    st.session_state.debate_active = False
if "debate_finished" not in st.session_state:
    st.session_state.debate_finished = False

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