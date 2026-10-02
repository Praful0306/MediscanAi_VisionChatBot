import asyncio
import streamlit as st
from google import genai
from google.genai import types
from telegram import Bot
from prompts import SUMMARY_REQUEST_PROMPT, SYSTEM_PROMPT, WELCOME_MESSAGE_TEMPLATE

# ==============================================================================
# 1. Configuration & Model Setup
# ==============================================================================
# We use gemini-2.5-flash: high speed, multimodal (text + vision), and cost-efficient.
MODEL_NAME = "gemini-3.5-flash"
st.set_page_config(page_title="MediScan AI", page_icon="💊", layout="centered")

# Read secrets from Streamlit secrets (configured locally in .streamlit/secrets.toml)
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
TELEGRAM_BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]

# ==============================================================================
# 2. Cached Gemini Client Connection
# ==============================================================================
# Why @st.cache_resource?
# Streamlit re-executes the script from top to bottom on every user interaction.
# Without caching, a brand new client is created and the old one is garbage collected,
# which causes "Cannot send a request, as the client has been closed."
# Wrapping this in @st.cache_resource keeps one connection alive across reruns.
@st.cache_resource
def get_gemini_client():
    return genai.Client(api_key=GEMINI_API_KEY)

gemini_client = get_gemini_client()


# ==============================================================================
# 3. Helper Functions: Chat UI & Communication
# ==============================================================================
def render_message(message):
    """Renders a single message (text or uploaded image) in the chat bubble."""
    with st.chat_message(message["role"]):
        if message["kind"] == "text":
            st.write(message["content"])
        elif message["kind"] == "image":
            st.image(message["content"])


def add_message(role, kind, content):
    """Appends a new message to session state and displays it immediately."""
    st.session_state.messages.append({"role": role, "kind": kind, "content": content})
    render_message(st.session_state.messages[-1])


def ask_gemini(parts):
    """Sends user content (text and/or image bytes) to the active Gemini chat."""
    try:
        response = st.session_state.chat.send_message(parts)
        return response.text
    except Exception as error:
        return f"⚠️ Sorry, something went wrong while analyzing: {error}"


def send_telegram(chat_id, text):
    """Sends the compiled medication schedule to the user's Telegram."""
    try:
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        target_id = str(chat_id).strip()
        bot_info = asyncio.run(bot.get_me())

        # If user inadvertently entered the bot's own ID or an invalid ID,
        # automatically resolve to the real user who messaged the bot!
        if target_id == str(bot_info.id) or not target_id.isdigit():
            updates = asyncio.run(bot.get_updates())
            for u in reversed(updates):
                if u.message and str(u.message.chat_id) != str(bot_info.id):
                    target_id = str(u.message.chat_id)
                    break

        asyncio.run(bot.send_message(chat_id=target_id, text=text))
        return True, "Success"
    except Exception as error:
        # Secondary fallback: try recent updates if initial send threw error
        try:
            bot = Bot(token=TELEGRAM_BOT_TOKEN)
            bot_info = asyncio.run(bot.get_me())
            updates = asyncio.run(bot.get_updates())
            for u in reversed(updates):
                if u.message and str(u.message.chat_id) != str(bot_info.id):
                    asyncio.run(bot.send_message(chat_id=u.message.chat_id, text=text))
                    return True, "Success"
        except Exception:
            pass
        return False, str(error)


# ==============================================================================
# 4. Step 1: Onboarding Screen (Shown once per session)
# ==============================================================================
if "onboarded" not in st.session_state:
    st.title("💊 MediScan AI")
    st.caption("Snap your medicine strip, label, or prescription. Get instructions & schedules on Telegram.")

    with st.form("onboarding_form"):
        name = st.text_input("Your Name", placeholder="e.g. Rahul")
        telegram_chat_id = st.text_input(
            "Telegram Chat ID",
            placeholder="e.g. 123456789",
            help="Your numeric Telegram Chat ID to receive automated updates directly on Telegram.",
        )
        submitted = st.form_submit_button("Let's go 🚀")

        if submitted:
            if not name.strip() or not telegram_chat_id.strip():
                st.warning("Please fill in both your name and Telegram Chat ID.")
            else:
                st.session_state.name = name.strip()
                st.session_state.telegram_chat_id = telegram_chat_id.strip()

                # Initialize the Gemini chat session with SYSTEM_PROMPT personality
                st.session_state.chat = gemini_client.chats.create(
                    model=MODEL_NAME,
                    config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
                )
                st.session_state.messages = []
                st.session_state.onboarded = True
                st.rerun()

    st.stop()


# ==============================================================================
# 5. Step 2: Main Chat Interface & Telegram Action Button
# ==============================================================================
header_col, button_col = st.columns([5, 2], vertical_alignment="center")

with header_col:
    st.title("💊 MediScan AI")

with button_col:
    # Disable button until there is at least one completed conversation exchange
    send_disabled = len(st.session_state.messages) <= 2
    if st.button("📲 Send to Telegram", disabled=send_disabled, use_container_width=True):
        with st.spinner("Compiling your medication schedule..."):
            summary = ask_gemini([SUMMARY_REQUEST_PROMPT])
            success, info = send_telegram(st.session_state.telegram_chat_id, summary)
            if success:
                st.success("Sent! Check your Telegram 📲")
            else:
                st.error(f"Couldn't send to Telegram: {info}")

st.caption(f"Logged in as **{st.session_state.name}** • Telegram Chat ID: `{st.session_state.telegram_chat_id}`")

# Render previous conversation history from session state
if not st.session_state.messages:
    add_message("assistant", "text", WELCOME_MESSAGE_TEMPLATE.format(name=st.session_state.name))
else:
    for message in st.session_state.messages:
        render_message(message)


# ==============================================================================
# 6. Step 3: Handling Input (Text & Medicine Photos)
# ==============================================================================
user_input = st.chat_input(
    "Ask a question, or attach a photo of your medicine...",
    accept_file=True,
    file_type=["jpg", "jpeg", "png"],
)

if user_input:
    photo = user_input.files[0] if user_input.files else None
    text = user_input.text
    parts = []

    # 1. Handle uploaded medicine image
    if photo is not None:
        photo_bytes = photo.getvalue()
        add_message("user", "image", photo_bytes)
        # Pass image bytes directly to Gemini Vision API
        parts.append(types.Part.from_bytes(data=photo_bytes, mime_type=photo.type))

    # 2. Handle accompanying or standalone text
    if text:
        add_message("user", "text", text)
        parts.append(text)
    elif photo is not None:
        # Default prompt if photo was uploaded without a caption
        parts.append(
            "Please identify this medicine, explain what it is used for, "
            "how to take it, and key safety precautions."
        )

    # 3. Request analysis from Gemini and display response
    with st.spinner("Analyzing medication details..."):
        answer = ask_gemini(parts)
        add_message("assistant", "text", answer)
