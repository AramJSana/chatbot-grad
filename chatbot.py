import streamlit as st
import os
from openai import AzureOpenAI
from dotenv import load_dotenv
load_dotenv()

MODEL = "gpt-4o"

client = AzureOpenAI(
    api_key         = os.environ["AZURE_OPENAI_API_KEY"],
    api_version     = "2025-04-01-preview",
    azure_endpoint  = "https://ai-proxy.lab.epam.com"
)