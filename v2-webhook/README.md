# 🌐 Version 2: Webhook Deployment

This version is for **24/7 hosting** on PythonAnywhere. It uses Webhooks so the bot stays online without needing your computer to be on.

---

### 🛠️ Setup & Installation

#### 1. Install Libraries
Run this command in your PythonAnywhere Bash Console:
pip install flask requests groq apify-client python-telegram-bot


#### 2. Update Credentials
Open `flask_app.py` and replace the placeholders with your actual API keys for Telegram, Groq, Apify, and Meta.

#### 3. Setup Webhook
Paste this URL into your browser to link Telegram to your server:
https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://<USERNAME>.pythonanywhere.com/<TOKEN>


#### 4. Reload Web App
Go to the **Web Tab** on PythonAnywhere and click the green **Reload** button. This "wakes up" the bot with your new code.

---

### ✨ What this bot does:
* **Scrapes Reels:** Automatically downloads videos via Apify.
* **AI Captions:** Writes viral text using Llama 3 (Groq).
* **Auto-Posts:** Uploads directly to Instagram via Meta API.
* **Background Processing:** Uses threads so the server never crashes.
