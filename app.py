import streamlit as st
import streamlit.components.v1 as components
import base64
import google.generativeai as genai
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def load_prompt():
    with open("prompts/researcher_prompt.txt", "r") as f:
        return f.read()

def save_chat_history(messages):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"chat_history_{timestamp}.txt"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"Hula Researcher Chat - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*80 + "\n\n")
        
        for msg in messages:
            role = "User" if msg["role"] == "user" else "Researcher"
            content = msg["parts"][0] if isinstance(msg.get("parts"), list) else msg.get("content", "")
            f.write(f"{role}:\n{content}\n\n")
            f.write("-"*80 + "\n\n")
    
    return filename

st.set_page_config(page_title="Hula Researcher Chat", page_icon="🎨")

st.title("Hula Research Chat")
st.caption("Share your experience with AI-generated content")

if "messages" not in st.session_state:
    st.session_state.messages = []
    welcome_message = """Hello! 👋

I'm conducting research on user experience with AI-generated content for Hula app.

Hula helps users create amazing AI-generated photos and videos. I'd love to learn about your experience with similar tools!

To start, could you tell me: Do you currently use any AI tools for creating photos or videos?"""
    
    st.session_state.messages.append({"role": "model", "parts": [welcome_message]})
    
if "system_prompt" not in st.session_state:
    st.session_state.system_prompt = load_prompt()

if "model" not in st.session_state:
    st.session_state.model = genai.GenerativeModel(
        model_name="gemini-2.0-flash-exp",
        system_instruction=st.session_state.system_prompt
    )
    st.session_state.chat = st.session_state.model.start_chat(history=[])

# Display chat messages
for message in st.session_state.messages:
    role = "user" if message["role"] == "user" else "assistant"
    content = message["parts"][0] if isinstance(message.get("parts"), list) else message.get("content", "")
    with st.chat_message(role):
        st.markdown(content)

# Input area with text input and voice recorder side by side
col1, col2 = st.columns([5, 1])

with col1:
    prompt = st.chat_input("Type your message or use voice 🎤")

with col2:
    st.write("")  # Add some spacing to align with chat input
    audio_base64 = components.html(
        open("components/audio_recorder.html", "r").read(),
        height=50,
    )

# Handle text input
if prompt:
    st.session_state.messages.append({"role": "user", "parts": [prompt]})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        try:
            response = st.session_state.chat.send_message(prompt)
            full_response = response.text
            message_placeholder.markdown(full_response)
            
            st.session_state.messages.append({"role": "model", "parts": [full_response]})
            
        except Exception as e:
            message_placeholder.error(f"Error: {str(e)}")

# Handle voice input
if audio_base64 is not None and audio_base64 != "":
    with st.chat_message("user"):
        st.write("🎤 Voice message received")
    
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        try:
            # Decode base64 audio
            audio_bytes = base64.b64decode(audio_base64)
            
            # Save temporarily
            with open("temp_audio.wav", "wb") as f:
                f.write(audio_bytes)
            
            # Upload to Gemini
            uploaded_file = genai.upload_file(path="temp_audio.wav")
            response = st.session_state.chat.send_message(["Transcribe this audio and respond to what the person said:", uploaded_file])
            
            full_response = response.text
            message_placeholder.markdown(full_response)
            
            st.session_state.messages.append({"role": "model", "parts": [full_response]})
            
        except Exception as e:
            message_placeholder.error(f"Error: {str(e)}")

with st.sidebar:
    st.header("Chat Controls")
    
    if st.button("Save Chat History"):
        if st.session_state.messages:
            filename = save_chat_history(st.session_state.messages)
            st.success(f"Chat saved as {filename}")
        else:
            st.warning("No messages to save yet")
    
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.session_state.chat = st.session_state.model.start_chat(history=[])
        st.rerun()
    
    st.divider()
    st.caption(f"Messages: {len(st.session_state.messages)}")
