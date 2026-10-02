# 💊 MediScan AI — Visual Medication Assistant

MediScan AI is a friendly, intelligent medication assistant powered by Google Gemini Vision and Streamlit, featuring automated medication schedule delivery via Telegram.

Users can snap a photo of a medicine strip, bottle label, or prescription, and MediScan AI will decode the active ingredients, explain what it is used for, outline dosage timing, and highlight critical safety precautions. With a single click, users can send their personalized medication schedule directly to their Telegram.

---

## ✨ Features
- **Visual Medicine Recognition**: Upload medicine strip/bottle photos or type medicine names.
- **Multimodal AI with Gemini**: Powered by `google-genai` for accurate visual inspection and conversational reasoning.
- **Strict Guardrails**: Scoped specifically to medications and healthcare safety with built-in disclaimers.
- **Telegram Automation**: Sends clean, emoji-formatted daily dosage schedules straight to the user's phone.
- **Clean Architecture**: Strictly isolates system prompts (`prompts.py`) from application logic (`app.py`).

---

## 📁 Project Structure

```
├── .streamlit/
│   └── secrets.toml.example    # Template for API keys & secrets
├── .gitignore                  # Keeps local secrets & venv out of Git
├── requirements.txt            # Project dependencies
├── prompts.py                  # System persona, welcome message & summary prompt
├── app.py                      # Main Streamlit application
└── README.md                   # Project documentation
```

---

## 🚀 Getting Started Locally

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd <repo-folder>
```

### 2. Create and activate a virtual environment
- **Windows (PowerShell)**:
  ```powershell
  python -m venv venv
  .\venv\Scripts\Activate.ps1
  ```
- **macOS / Linux**:
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Secrets
Create a `.streamlit/secrets.toml` file by copying the template:
```bash
# On Windows PowerShell
Copy-Item .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Fill in your actual API keys in `.streamlit/secrets.toml`:
```toml
# Get your Gemini API key from https://aistudio.google.com
GEMINI_API_KEY = "your-gemini-api-key-here"

# Get your Telegram Bot Token from @BotFather on Telegram
TELEGRAM_BOT_TOKEN = "your-telegram-bot-token-here"
```

> **Note**: `.streamlit/secrets.toml` is excluded by `.gitignore` so your private credentials are never committed.

---

## 🤖 Getting Your Telegram Credentials

1. Open Telegram and search for **[@BotFather](https://t.me/BotFather)**.
2. Send `/newbot`, choose a name and username for your bot, and copy the **Bot Token**.
3. Search for your newly created bot on Telegram and press **Start** (or send any greeting message like "hello").
4. To find your **Telegram Chat ID**, message **[@userinfobot](https://t.me/userinfobot)** on Telegram — it will immediately reply with your numeric `Id`.

---

## 🏃 Running the Application

```bash
streamlit run app.py
```

The app will open automatically in your browser at `http://localhost:8501`.

1. Enter your Name and Telegram Chat ID on the onboarding screen.
2. Upload a photo of a medicine or type a question in the chat.
3. Click **"📲 Send to Telegram"** at the top right to receive your medication schedule!
