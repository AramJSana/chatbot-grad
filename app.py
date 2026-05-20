import streamlit as st
import os
from openai import AzureOpenAI

MODEL = "gpt-4o"

print(os.getenv('DIAL_KEY'))

client = AzureOpenAI(
    api_key         = os.getenv("DIAL_KEY"),
    api_version     = "2025-04-01-preview",
    azure_endpoint  = "https://ai-proxy.lab.epam.com"
)

st.title("Chatbot with SQL capabilities")

st.caption("Ask me anything about the sales data!")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": "You are a helpful assistant."}]

for message in st.session_state.messages:
    if message["role"] == "system":
        continue  # Skip displaying system messages
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("How can I help you?")
if prompt:
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)

    response = client.chat.completions.create(
        model=MODEL,
        messages=st.session_state.messages,
    )

    assistant_replied = (response.choices[0].message.content)
    # The response from the LLM will is added to the chat history
    st.session_state.messages.append({"role": "assistant", "content": assistant_replied})
    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        st.markdown(assistant_replied)