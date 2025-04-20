import streamlit as st
from pages.glucose_chat_agent import get_glucose_advice  # Changed from relative to absolute import

st.set_page_config(page_title="💬 Glucose Chat", layout="wide")

st.title("💬 Glucose Buddy Chat")

st.markdown("""
<style>
    .chat-container {
        background-color: #f9f9f9;
        border-radius: 12px;
        padding: 20px;
        margin: 20px 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask about managing your glucose levels..."):
    # Display user message
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Get AI response
    with st.spinner("Thinking..."):
        response = str(get_glucose_advice(prompt))
        
        # Display assistant response
        st.chat_message("assistant").markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})