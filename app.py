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

    res = client.chat.completions.create(
        messages=st.session_state.messages,
        model=MODEL,
        max_tokens=1024,
    )

    # OpenAI SDK returns a ChatCompletion object — use attributes
    choice_message = res.choices[0].message
    assistant_replied = choice_message.content

    # Some gateways return content as a list of parts instead of a string
    if isinstance(assistant_replied, list):
        assistant_replied = "".join(
            part.get("text", "")
            for part in assistant_replied
            if isinstance(part, dict) and part.get("type") == "text"
        )

    # Save and display
    st.session_state.messages.append({"role": "assistant", "content": assistant_replied})
    with st.chat_message("assistant"):
        st.markdown(assistant_replied)