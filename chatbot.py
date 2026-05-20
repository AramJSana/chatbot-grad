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