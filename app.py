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
