import streamlit as st
import os
from openai import OpenAI

MODEL = "databricks-gpt-oss-120b"

DB_TOKEN = os.environ.get('DB-TOKEN')

client = OpenAI(
  api_key=DB_TOKEN,
  base_url="https://dbc-9fa0f090-1c91.cloud.databricks.com/ai-gateway/mlflow/v1"
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
        messages=st.session_state.messages,
        model=MODEL,
        max_tokens=1024
    )


    assistant_replied = (response.choices[0].message.content)
    if isinstance(assistant_replied, list):
        combined_content = "".join([part.get("text", "") for part in assistant_replied if part.get("type") == "text"])
        reformatted_message = {
            "role": assistant_replied.get("role"),
            "content": combined_content
        }
        assistant_replied = reformatted_message["content"]
    # The response from the LLM will is added to the chat history
    st.session_state.messages.append({"role": "assistant", "content": assistant_replied})
    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        st.markdown(assistant_replied)