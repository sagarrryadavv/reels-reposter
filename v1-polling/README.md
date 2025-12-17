# Version 1: Local Polling Bot

This version of the bot uses the **Polling** method. It constantly "polls" (asks) Telegram for new messages. This is the best version for testing and development on your own computer.

### 🚀 How to Run Locally:
1. **Install requirements:**
   ```bash
   pip install python-telegram-bot requests groq apify-client
2. **Setup Credentials:**
Open `bot.py` and enter your API keys for Telegram, Groq, Apify, and Meta.

3. **Launch:**
   ```bash
   python bot.py
---

### ⚠️ Note
This bot will only work as long as your terminal/computer stays open. If you close your terminal or turn off your laptop, the bot goes offline.
