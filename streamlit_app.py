"""
streamlit_app.py

Streamlit front-end for the emergency support agent. Provides a
simple chat interface that calls main_controller.handle_user_request()
for each message and displays the response, along with an optional
debug view of the internal agent trace.
"""

import streamlit as st

from main_controller import handle_user_request

st.set_page_config(page_title="Emergency Support Assistant", page_icon="🆘")

st.title("🆘 Emergency Support Assistant")
st.caption(
    "This is a support tool, not a substitute for emergency services. "
    "If you are in immediate danger, contact your local emergency number directly."
)

# Session state holds chat history and a stable session_id for this browser session
if "messages" not in st.session_state:
    st.session_state.messages = []

if "session_id" not in st.session_state:
    import uuid
    st.session_state.session_id = str(uuid.uuid4())

# Sidebar: debug view toggle, useful while you're still testing
with st.sidebar:
    st.header("Debug")
    show_trace = st.checkbox("Show agent trace", value=False)
    if st.button("Clear conversation"):
        st.session_state.messages = []
        st.rerun()

# Render existing chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if show_trace and msg.get("trace"):
            with st.expander("Agent trace"):
                for line in msg["trace"]:
                    st.text(line)
if "country" not in st.session_state:
    st.session_state.country = None

if st.session_state.country is None:
    st.session_state.country = st.selectbox(
        "To show you relevant emergency numbers if needed, what's your country?",
        ["United States", "United Kingdom", "Pakistan", "India", "Other / Prefer not to say"],
    )
    st.stop()  # don't show chat until country is set
# Chat input
user_input = st.chat_input("What's going on?")

if user_input:
    # Show the user's message immediately
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # Process through the full system
    with st.chat_message("assistant"):
        with st.spinner("Processing..."):
            try:
                state = handle_user_request(
                    raw_input=user_input,
                    session_id=st.session_state.session_id,
                )
                response_text = state.final_response or "I wasn't able to generate a response — please try again."
                trace_lines = [f"{r.agent_name} | {r.status}" for r in state.agent_trace]

                if state.crisis_flag:
                    st.error("⚠️ This message was flagged for urgent attention.")

            except Exception as exc:
                import traceback
                response_text = (
                    "Something went wrong processing your message. "
                    "If this is urgent, please contact emergency services directly."
                )
                trace_lines = [f"ERROR: {type(exc).__name__}: {exc}"] + traceback.format_exc().splitlines()

        st.write(response_text)
        if show_trace:
            with st.expander("Agent trace"):
                for line in trace_lines:
                    st.text(line)

    st.session_state.messages.append({
        "role": "assistant",
        "content": response_text,
        "trace": trace_lines,
    })