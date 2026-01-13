import streamlit as st
import anthropic
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

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
            f.write(f"{role}:\n{msg['content']}\n\n")
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

**To start, could you tell me:**
- Do you currently use any AI tools for creating photos or videos?
- If yes, which ones and what do you create with them?"""
    
    st.session_state.messages.append({"role": "assistant", "content": welcome_message})
    
if "system_prompt" not in st.session_state:
    st.session_state.system_prompt = load_prompt()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Share your thoughts..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                system=st.session_state.system_prompt,
                messages=st.session_state.messages
            )
            
            full_response = response.content[0].text
            message_placeholder.markdown(full_response)
            
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
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
        st.rerun()
    
    st.divider()
    st.caption(f"Messages: {len(st.session_state.messages)}")
