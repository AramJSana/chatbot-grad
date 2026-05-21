import os
import json
import streamlit as st
from openai import OpenAI
from databricks import sql

MODEL = "databricks-gpt-oss-120b"

def main() -> None:
    st.title("Chatbot with SQL capabilities")
    st.caption("Ask me anything about the sales data!")

    client = get_openai_client()

    with open("systemprompt.md", "r") as file:
        system_prompt = file.read()

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "system",
             "content": system_prompt}
        ]

    for m in st.session_state.messages:
        if m["role"] in ("system", "tool"):
            continue
        if not m.get("content"):
            continue
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    prompt = st.chat_input("How can I help you?")
    if not prompt:
        return

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # tool-calling loop with a max attempt count of 3
    for _ in range(3):
        res = client.chat.completions.create(
            model=MODEL,
            messages=st.session_state.messages,
            tools=TOOLS,
            tool_choice="auto",
            max_tokens=1024,
        )
        msg = res.choices[0].message

        # If the model wants to call tools, run them and loop again
        if msg.tool_calls:
            st.session_state.messages.append({
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [tc.model_dump() for tc in msg.tool_calls],
            })
            for tc in msg.tool_calls:
                args = json.loads(tc.function.arguments or "{}")
                if tc.function.name == "sql_query":
                    result = sql_query(args.get("query", ""))
                else:
                    result = json.dumps({"error": f"unknown tool {tc.function.name}"})
                st.session_state.messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                })
            continue

        # If no tool calls, return answer
        content = msg.content or ""
        if isinstance(content, list):
            content = "".join(
                p.get("text", "") for p in content
                if isinstance(p, dict) and p.get("type") == "text"
            )
        st.session_state.messages.append({"role": "assistant", "content": content})
        with st.chat_message("assistant"):
            st.markdown(content)
        break


# Using streamlit decorator to cache as to not run them every time
@st.cache_resource
def get_openai_client():
    token = os.getenv("DB-TOKEN")
    if not token:
        st.error("Couldn't retrieve OpenAI token.")
        st.stop()
    return OpenAI(
        api_key=token,
        base_url="https://dbc-9fa0f090-1c91.cloud.databricks.com/ai-gateway/mlflow/v1",
    )


@st.cache_resource
def get_sql_connection():
    token = os.getenv("SQL-TOKEN")
    if not token:
        st.error("Couldn't retrieve SQL token.")
        st.stop()
    return sql.connect(
        server_hostname="dbc-9fa0f090-1c91.cloud.databricks.com",
        http_path="/sql/1.0/warehouses/89b5917496df409a",
        access_token=token,
    )


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "sql_query",
            "description": "Execute a read-only SQL query on the connected Databricks warehouse.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The SQL query to execute",
                    }
                },
                "required": ["query"],
            },
        },
    }
]


def sql_query(query: str) -> str:
    connection = get_sql_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            cols = [d[0] for d in cursor.description] if cursor.description else []
        return json.dumps({"columns": cols, "rows": [list(r) for r in rows]}, default=str)
    except Exception as exception:
        return json.dumps({"error": str(exception)})


main()