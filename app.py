import json
import streamlit as st
import os
import asyncio
from dotenv import load_dotenv
from groq import Groq
from hindsight_client import Hindsight

load_dotenv()

# ---------------- PAGE CONFIG ----------------

st.set_page_config(
    page_title="SmartSupport AI",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 SmartSupport AI")
st.caption("AI Customer Support with Long-Term Memory")

# ---------------- API CONFIG ----------------

groq_key = os.getenv("GROQ_API_KEY")
hindsight_key = os.getenv("HINDSIGHT_API_KEY")
hindsight_url = os.getenv("HINDSIGHT_BASE_URL")
bank_id = os.getenv("HINDSIGHT_BANK_ID")

if not all([groq_key, hindsight_key, hindsight_url, bank_id]):
    st.error("Check your API settings in the .env file.")
    st.stop()

groq_client = Groq(api_key=groq_key)


# ---------------- HINDSIGHT FUNCTIONS ----------------

async def recall_async(query):
    client = Hindsight(
        base_url=hindsight_url,
        api_key=hindsight_key
    )
    try:
        return await client.arecall(
            bank_id=bank_id,
            query=query
        )
    finally:
        await client.aclose()


def recall_memory(query):
    return asyncio.run(recall_async(query))


async def retain_async(content):
    client = Hindsight(
        base_url=hindsight_url,
        api_key=hindsight_key
    )
    try:
        return await client.aretain(
            bank_id=bank_id,
            content=content,
            context="Customer support conversation"
        )
    finally:
        await client.aclose()


def save_memory(content):
    return asyncio.run(retain_async(content))

def extract_customer_profile(memories):

    if not memories:
        return {}

    memory_text = "\n".join(memories)

    response = groq_client.chat.completions.create(
        model="openai/gpt-oss-120b",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": """
                Extract customer information from the memories.
                Return valid JSON with these keys:
                name, order_number, support_preference.

                Use null if information is unavailable.
                Never invent customer information.
                """
            },
            {
                "role": "user",
                "content": memory_text
            }
        ]
    )

    return json.loads(
        response.choices[0].message.content
    )



# ---------------- SESSION STATE ----------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_memories" not in st.session_state:
    st.session_state.last_memories = []

if "memory_status" not in st.session_state:
    st.session_state.memory_status = "Not checked"


# ---------------- CUSTOMER PROFILE ----------------

st.sidebar.title("👤 Customer Profile")

customer_id = st.sidebar.text_input(
    "Customer ID",
    value="customer-001"
)

st.sidebar.info(
    "Customer conversations are stored in Hindsight."
)

# ---------------- DASHBOARD AND CHAT TABS ----------------

dashboard_tab, chat_tab = st.tabs(
    ["📊 Customer Dashboard", "💬 AI Chat"]
)


# ==================================================
# CUSTOMER DASHBOARD
# ==================================================

with dashboard_tab:

    st.subheader("👤 Customer Profile Details")

    if st.session_state.last_memories:

        try:
            profile = extract_customer_profile(
                st.session_state.last_memories
            )

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "Customer Name",
                    profile.get("name") or "Not found"
                )

            with col2:
                st.metric(
                    "Order Number",
                    profile.get("order_number") or "Not found"
                )

            with col3:
                st.metric(
                    "Support Preference",
                    profile.get("support_preference") or "Not found"
                )

        except Exception as e:
            st.warning(f"Profile extraction error: {e}")

    else:
        st.info("Retrieve customer memories to extract profile details.")

    st.subheader("🧠 Customer Memory")
    st.header("📊 Customer Memory Dashboard")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Customer ID",
            customer_id
        )

    with col2:
        st.metric(
            "Chat Messages",
            len(st.session_state.messages)
        )

    with col3:
        st.metric(
            "Memories Retrieved",
            len(st.session_state.last_memories)
        )

    st.divider()

    st.subheader("🧠 Customer Memory")

    if st.button("🔄 Retrieve Customer Memories"):

        try:
            with st.spinner("Loading customer memories..."):

                result = recall_memory(
                f"Customer ID: {customer_id}. "
                "What is my name, order number, and "
                "preferred support method?"
                )
            

                st.session_state.last_memories = [
                    item.text for item in result.results
                ]

                st.session_state.memory_status = "Successfully retrieved"

           
            st.success("Customer memories retrieved!")
            st.rerun()

        except Exception as e:
            st.session_state.memory_status = "Retrieval failed"
            st.error(f"Memory error: {e}")


        except Exception as e:
            st.session_state.memory_status = "Retrieval failed"
            st.error(f"Memory error: {e}")

    st.write(
        "Memory status:",
        st.session_state.memory_status
    )

    if st.session_state.last_memories:

        for index, memory in enumerate(
            st.session_state.last_memories,
            start=1
        ):

            with st.expander(f"Memory {index}"):

                st.write(memory)

    else:
        st.info(
            "Click 'Retrieve Customer Memories' to view saved information."
        )

    st.divider()

    st.subheader("📜 Conversation History")

    if st.session_state.messages:

        for message in st.session_state.messages:

            with st.chat_message(message["role"]):
                st.write(message["content"])

    else:
        st.info("No conversations in this session yet.")


# ==================================================
# AI CHAT
# ==================================================

with chat_tab:

    st.header("💬 SmartSupport AI Chat")

    for message in st.session_state.messages:

        with st.chat_message(message["role"]):
            st.write(message["content"])

    user_input = st.chat_input(
        "Describe your problem..."
    )

    if user_input:

        with st.chat_message("user"):
            st.write(user_input)

        memories = []

        try:
            with st.spinner("Recalling customer memories..."):

                result = recall_memory(
                    f"Customer ID: {customer_id}. "
                    f"Find previous support details and preferences "
                    f"relevant to: {user_input}"
                )

                memories = [
                    item.text for item in result.results
                ]

                st.session_state.last_memories = memories
                st.session_state.memory_status = "Successfully retrieved"

        except Exception as e:
            st.warning(f"Memory recall error: {e}")

        memory_context = "\n".join(memories)

        system_prompt = f"""
        You are SmartSupport AI, a friendly customer support assistant.

        Give simple and helpful solutions.

        Current customer ID: {customer_id}

        Relevant customer memories:
        {memory_context}

        Use memories only when relevant.
        Do not invent customer history.
        """

        try:

            with st.chat_message("assistant"):

                with st.spinner("Thinking..."):

                    response = groq_client.chat.completions.create(
                        model="openai/gpt-oss-120b",
                        messages=[
                            {
                                "role": "system",
                                "content": system_prompt
                            },
                            *st.session_state.messages,
                            {
                                "role": "user",
                                "content": user_input
                            }
                        ]
                    )

                    answer = response.choices[0].message.content

                    st.write(answer)

            st.session_state.messages.append({
                "role": "user",
                "content": user_input
            })

            st.session_state.messages.append({
                "role": "assistant",
                "content": answer
            })

            try:

                with st.spinner("Saving customer memory..."):

                    save_memory(
                        f"Customer ID: {customer_id}\n"
                        f"Customer message: {user_input}\n"
                        f"Assistant response: {answer}"
                    )

                st.success("Customer memory saved successfully!")

            except Exception as e:
                st.warning(f"Memory save error: {e}")

        except Exception as e:
            st.error(f"Groq error: {e}")
