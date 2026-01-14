import streamlit as st
from streamlit_chat import message
import streamlit.components.v1 as components
import google.generativeai as genai
import base64
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
            role = "User" if msg["is_user"] else "Assistant"
            f.write(f"{role}:\n{msg['message']}\n\n")
            f.write("-"*80 + "\n\n")
    
    return filename

st.set_page_config(page_title="Hula Researcher Chat", page_icon="🎨")

st.title("Hula Research Chat")
st.caption("Share your experience with AI-generated content")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
    welcome_message = """Hello! 👋

I'm conducting research on user experience with AI-generated content for Hula app.

Hula helps users create amazing AI-generated photos and videos. I'd love to learn about your experience with similar tools!

To start, could you tell me: Do you currently use any AI tools for creating photos or videos?"""
    
    st.session_state.messages.append({"message": welcome_message, "is_user": False})

if "last_audio" not in st.session_state:
    st.session_state.last_audio = ""
    
if "system_prompt" not in st.session_state:
    st.session_state.system_prompt = load_prompt()

if "model" not in st.session_state:
    st.session_state.model = genai.GenerativeModel(
        model_name="gemini-2.0-flash-exp",
        system_instruction=st.session_state.system_prompt
    )
    st.session_state.chat = st.session_state.model.start_chat(history=[])

# Display chat messages using streamlit-chat
for i, msg in enumerate(st.session_state.messages):
    message(msg["message"], is_user=msg["is_user"], key=str(i))

# Chat input area - at the bottom
col1, col2 = st.columns([11, 1])

with col1:
    user_input = st.text_input("Type your message...", key="user_input", label_visibility="collapsed")

with col2:
    audio_base64 = components.html(
        open("components/audio_recorder.html", "r").read(),
        height=48
    )

# Handle text input
if user_input and st.session_state.get("last_input") != user_input:
    st.session_state["last_input"] = user_input
    st.session_state.messages.append({"message": user_input, "is_user": True})
    
    try:
        response = st.session_state.chat.send_message(user_input)
        full_response = response.text
        st.session_state.messages.append({"message": full_response, "is_user": False})
        st.rerun()
    except Exception as e:
        st.error(f"Error: {str(e)}")

# Handle voice input
if audio_base64 is not None and isinstance(audio_base64, str) and audio_base64 != "" and audio_base64 != st.session_state.get("last_audio", ""):
    st.session_state["last_audio"] = audio_base64
    
    try:
        audio_bytes = base64.b64decode(audio_base64)
        
        with open("temp_audio.wav", "wb") as f:
            f.write(audio_bytes)
        
        uploaded_file = genai.upload_file(path="temp_audio.wav")
        transcription = st.session_state.chat.send_message(["Transcribe this audio to text only, no commentary:", uploaded_file])
        text_content = transcription.text.strip()
        
        st.session_state.messages.append({"message": text_content, "is_user": True})
        
        response = st.session_state.chat.send_message(text_content)
        full_response = response.text
        st.session_state.messages.append({"message": full_response, "is_user": False})
        
        if os.path.exists("temp_audio.wav"):
            os.remove("temp_audio.wav")
        st.rerun()
        
    except Exception as e:
        st.error(f"Error processing audio: {str(e)}")

# Sidebar
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
