import streamlit as st
import os
from openai import OpenAI
from databricks import sql

def main():

    MODEL = "databricks-gpt-oss-120b"

    DB_TOKEN = os.getenv("DB_TOKEN")

    SQL_TOKEN = os.getenv("SQL_TOKEN")

    connection = sql.connect(
                            server_hostname = "dbc-9fa0f090-1c91.cloud.databricks.com",
                            http_path = "/sql/1.0/warehouses/89b5917496df409a",
                            access_token = SQL_TOKEN
                            )

    cursor = connection.cursor()

    client = OpenAI(
                    api_key=DB_TOKEN,
                    base_url="https://dbc-9fa0f090-1c91.cloud.databricks.com/ai-gateway/mlflow/v1"
                    )
    
    tools = [
        {
            "type": "function",
            "function": {
                "name": "sql_query",
                "description": "Execute a SQL query on the connected database",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The SQL query to execute"
                        },
                        "cursor": {
                            "type": "object",
                            "description": "The database cursor to use for executing the query"
                        }
                    }
                }
            }
        }
    ]

    st.title("Chatbot with SQL capabilities")

    st.caption("Ask me anything about the sales data!")

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "system", "content": "You are a helpful assistant with access to a SQL warehouse."}]

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
            messages    = st.session_state.messages,
            model       = MODEL,
            max_tokens  = 1024,
            tools       = tools,
            tool_choice = "auto"
        )

        # OpenAI SDK returns a ChatCompletion object — use attributes
        choice_message = res.choices[0].message
        assistant_replied = choice_message.content

        # If the gateway returns a list as a response, concatenates it into a single string
        if isinstance(assistant_replied, list):
            assistant_replied = "".join(
                part.get("text", "")
                for part in assistant_replied
                if isinstance(part, dict) and part.get("type") == "text"
            )

        st.session_state.messages.append({"role": "assistant", "content": assistant_replied})
        with st.chat_message("assistant"):
            st.markdown(assistant_replied)


def sql_query(query, cursor):
    try:
        cursor.execute(query)
        results = cursor.fetchall()
        return results
    except Exception as e:
        return f"Error executing query: {e}"