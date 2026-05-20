import streamlit as st
import os
from openai import AzureOpenAI

MODEL = "gpt-4o"

client = AzureOpenAI(
    api_key         = dbutils.secrets.get(scope="dbrickstoken", key="dialtoken"),
    api_version     = "2025-04-01-preview",
    azure_endpoint  = "https://ai-proxy.lab.epam.com"
)