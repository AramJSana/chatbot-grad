import os
import json
import streamlit as st
from openai import OpenAI
from databricks import sql


MODEL = "databricks-gpt-oss-120b"
MAX_AGENT_STEPS = 8
LLM_TIMEOUT_SECONDS = 60
MAX_ROWS_TO_LLM = 50
SQL_RETRY_ATTEMPTS = 2

DATABRICKS_HOST = "dbc-9fa0f090-1c91.cloud.databricks.com"
SQL_HTTP_PATH = "/sql/1.0/warehouses/89b5917496df409a"

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

def main() -> None:
    st.title("Chatbot with SQL capabilities")
    st.caption("Ask me anything about the bike sales data!")

    client = get_openai_client()

    
    if "_system_prompt" not in st.session_state:
        with open("systemprompt.md", "r") as f:
            st.session_state["_system_prompt"] = f.read()

    # message history
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "system", "content": st.session_state["_system_prompt"]}
        ]

    # Sidebar: reset button
    with st.sidebar:
        if st.button("Clear conversation"):
            st.session_state.messages = [
                {"role": "system", "content": st.session_state["_system_prompt"]}
            ]
            reset_sql_connection()
            st.rerun()

    # Render chat
    for m in st.session_state.messages:
        if m["role"] in ("system", "tool"):
            continue
        if m["role"] == "assistant" and not m.get("content"):
            continue
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    
    prompt = st.chat_input("How can I help you?")
    if not prompt:
        return

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Run the agent inside a single assistant chat bubble
    with st.chat_message("assistant"):
        placeholder = st.empty()
        run_agent(client, placeholder)

@st.cache_resource
def get_openai_client() -> OpenAI:
    token = os.getenv("DB-TOKEN")
    if not token:
        st.error("Couldn't retrieve OpenAI token (env var `DB-TOKEN`).")
        st.stop()
    return OpenAI(
        api_key=token,
        base_url=f"https://{DATABRICKS_HOST}/ai-gateway/mlflow/v1",
    )


def open_sql_connection():
    token = os.getenv("SQL-TOKEN")
    if not token:
        st.error("Couldn't retrieve SQL token (env var `SQL-TOKEN`).")
        st.stop()
    return sql.connect(
        server_hostname=DATABRICKS_HOST,
        http_path=SQL_HTTP_PATH,
        access_token=token,
    )


def get_sql_connection():
    connection = st.session_state.get("_sql_conn")
    if connection is None:
        connection = open_sql_connection()
        st.session_state["_sql_conn"] = connection
    return connection


def reset_sql_connection() -> None:
    """Drop the cached SQL connection so the next call reconnects."""
    connection = st.session_state.pop("_sql_conn", None)
    if connection is not None:
        try:
            connection.close()
        except Exception:
            pass


def sql_query(query: str) -> str:
    last_error: Exception | None = None

    for attempt in range(SQL_RETRY_ATTEMPTS):
        try:
            connection = get_sql_connection()
            with connection.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                cols = [d[0] for d in cursor.description] if cursor.description else []

            truncated = len(rows) > MAX_ROWS_TO_LLM
            payload = {
                "columns": cols,
                "rows": [list(r) for r in rows[:MAX_ROWS_TO_LLM]],
                "row_count": len(rows),
                "truncated": truncated,
            }
            return json.dumps(payload, default=str)

        except Exception as exc:
            last_error = exc
            reset_sql_connection()  # force reconnect on next attempt

    return json.dumps({"error": f"{type(last_error).__name__}: {last_error}"})


def run_agent(client: OpenAI, placeholder) -> None:
    """Run the tool-calling loop and render the final assistant message."""
    for step in range(MAX_AGENT_STEPS):
        with st.spinner(f"Thinking… (step {step + 1}/{MAX_AGENT_STEPS})"):
            try:
                res = client.chat.completions.create(
                    model=MODEL,
                    messages=st.session_state.messages,
                    tools=TOOLS,
                    tool_choice="auto",
                    max_tokens=1024,
                    timeout=LLM_TIMEOUT_SECONDS,
                )
            except Exception as exc:
                placeholder.error(f"LLM call failed: {type(exc).__name__}: {exc}")
                return

        msg = res.choices[0].message

        # tool call
        if msg.tool_calls:
            st.session_state.messages.append({
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [tc.model_dump() for tc in msg.tool_calls],
            })

            for tc in msg.tool_calls:
                args = json.loads(tc.function.arguments or "{}")
                if tc.function.name == "sql_query":
                    query = args.get("query", "")
                    with st.expander(f"🔎 SQL (step {step + 1})", expanded=False):
                        st.code(query, language="sql")
                    with st.spinner("Running SQL on the warehouse…"):
                        result = sql_query(query)
                else:
                    result = json.dumps({"error": f"unknown tool {tc.function.name}"})

                try:
                    parsed = json.loads(result)
                    if isinstance(parsed, dict) and "error" in parsed:
                        st.warning(f"Tool error: {parsed['error']}")
                except json.JSONDecodeError:
                    pass

                st.session_state.messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                })
            continue

        content = msg.content or ""
        if isinstance(content, list):
            content = "".join(
                p.get("text", "") for p in content
                if isinstance(p, dict) and p.get("type") == "text"
            )
        st.session_state.messages.append({"role": "assistant", "content": content})
        placeholder.markdown(content or "_(empty response)_")
        return

    placeholder.error(
        f"Agent reached the step limit without producing a final "
        "answer. Please try again."
    )


main()