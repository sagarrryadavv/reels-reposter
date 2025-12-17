import os
import requests
import asyncio
import threading
import time
from flask import Flask, request

# --- PROXY SETTINGS (Crucial for PythonAnywhere Free Tier) ---
os.environ['http_proxy'] = "http://proxy.server:3128"
os.environ['https_proxy'] = "http://proxy.server:3128"

# --- CREDENTIALS ---
TELEGRAM_TOKEN = "YOUR_TELEGRAM_TOKEN"
GROQ_API_KEY = "YOUR_GROQ_API_KEY"
APIFY_TOKEN = "YOUR_APIFY_TOKEN"
INSTAGRAM_BUSINESS_ID = "YOUR_INSTAGRAM_BUSINESS_ID"
INSTAGRAM_ACCESS_TOKEN = "YOUR_INSTAGRAM_ACCESS_TOKEN"

app = Flask(__name__)

def run_bot_logic(url, chat_id):
    """
    This function handles the heavy lifting in a background thread.
    Imports are inside the function to ensure the Web App starts even if a library is missing.
    """
    try:
        from groq import Groq
        from apify_client import ApifyClient
        
        # Initial status update
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                     data={"chat_id": chat_id, "text": "🚀 Connection Secure. Starting Step 1..."})

        # 1. APIFY SCRAPER (Step 1)
        # Note: We rely on os.environ proxy settings for compatibility
        apify_client = ApifyClient(token=APIFY_TOKEN)
        
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                     data={"chat_id": chat_id, "text": "🔍 Step 1: Running Apify Scraper..."})
        
        run = apify_client.actor("apify/instagram-scraper").call(
            run_input={"directUrls": [url], "resultsType": "details"}
        )
        
        dataset_items = list(apify_client.dataset(run["defaultDatasetId"]).iterate_items())
        if not dataset_items:
            raise Exception("Apify finished but no video data was found. Check the Reel link.")
            
        item = dataset_items[0]
        video_url = item.get("videoUrl")
        owner_handle = item.get("ownerUsername", "creator")
        
        # Download video bytes via proxy
        video_response = requests.get(video_url, stream=True)
        video_bytes = video_response.content

        # 2. AI CAPTION (Step 2)
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                     data={"chat_id": chat_id, "text": f"🤖 Step 2: Generating AI caption for @{owner_handle}..."})
        
        groq_client = Groq(api_key=GROQ_API_KEY)
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile", 
            messages=[{"role":"user","content":f"Write a viral Gen Z caption for a Reel. Tag @{owner_handle} for credit. 3 hashtags."}]
        )
        ai_caption = completion.choices[0].message.content

        # 3. INSTAGRAM UPLOAD (Step 3 & 4)
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                     data={"chat_id": chat_id, "text": "📡 Step 3: Initializing Meta container..."})
        
        # Init container
        init_res = requests.post(f"https://graph.facebook.com/v21.0/{INSTAGRAM_BUSINESS_ID}/media", data={
            "media_type": "REELS", 
            "upload_type": "resumable", 
            "caption": ai_caption, 
            "access_token": INSTAGRAM_ACCESS_TOKEN
        }).json()
        
        container_id = init_res.get('id')
        if not container_id:
            raise Exception(f"Meta Init Error: {init_res.get('error', {}).get('message')}")

        # Upload bytes
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                     data={"chat_id": chat_id, "text": "⬆️ Step 4: Uploading video bytes..."})
        
        requests.post(f"https://rupload.facebook.com/ig-api-upload/v21.0/{container_id}", 
                      headers={
                          "Authorization": f"OAuth {INSTAGRAM_ACCESS_TOKEN}", 
                          "offset": "0", 
                          "file_size": str(len(video_bytes))
                      },
                      data=video_bytes)

        # 4. PUBLISH (Step 5)
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                     data={"chat_id": chat_id, "text": "⏳ Step 5: Waiting 45s for Meta processing..."})
        
        time.sleep(45)
        
        publish_res = requests.post(f"https://graph.facebook.com/v21.0/{INSTAGRAM_BUSINESS_ID}/media_publish", 
                                   data={
                                       "creation_id": container_id, 
                                       "access_token": INSTAGRAM_ACCESS_TOKEN
                                   }).json()

        if "id" in publish_res:
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                         data={"chat_id": chat_id, "text": f"✅ SUCCESS! Reel is live.\n\nAI Caption:\n{ai_caption}"})
        else:
            raise Exception(f"Meta Publish Error: {publish_res.get('error', {}).get('message')}")

    except Exception as e:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                     data={"chat_id": chat_id, "text": f"⚠️ Fatal Error: {str(e)}"})

@app.route(f'/{TELEGRAM_TOKEN}', methods=['POST'])
def webhook():
    """Receiver that handles Telegram data and starts the background thread."""
    try:
        update = request.get_json()
        if update and "message" in update:
            msg = update["message"]
            chat_id = msg["chat"]["id"]
            text = msg.get("text", "")
            
            if text.startswith("http"):
                # Start a thread to prevent the Flask worker from timing out (500 Error)
                thread = threading.Thread(target=run_bot_logic, args=(text, chat_id))
                thread.start()
                
        return "OK", 200
    except Exception:
        return "Error", 500

@app.route('/')
def home():
    return "Bot Server is Live", 200