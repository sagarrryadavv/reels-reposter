import os
import requests
import asyncio
from groq import Groq
from apify_client import ApifyClient
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# --- FINAL CREDENTIALS ---
TELEGRAM_TOKEN = "YOUR_TELEGRAM_TOKEN"
GROQ_API_KEY = "YOUR_GROQ_API_KEY"
APIFY_TOKEN = "YOUR_APIFY_TOKEN"
INSTAGRAM_BUSINESS_ID = "YOUR_INSTAGRAM_BUSINESS_ID"
INSTAGRAM_ACCESS_TOKEN = "YOUR_INSTAGRAM_ACCESS_TOKEN"

client = Groq(api_key=GROQ_API_KEY)
apify_client = ApifyClient(APIFY_TOKEN)

async def get_video_data_and_details(url):
    """Fetches video bytes and metadata via Apify."""
    run_input = { "directUrls": [url], "resultsType": "details" }
    run = apify_client.actor("apify/instagram-scraper").call(run_input=run_input)
    for item in apify_client.dataset(run["defaultDatasetId"]).iterate_items():
        v_url = item.get("videoUrl")
        owner_handle = item.get("ownerUsername", "the creator")
        response = requests.get(v_url, stream=True)
        return response.content, owner_handle
    return None, None

async def handle_reel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_url = update.message.text
    if not user_url.startswith("http"): return

    await update.message.reply_text("💎 Fetching video & identifying creator for tagging...")

    try:
        # 1. FETCH VIDEO & OWNER HANDLE
        video_data, owner_handle = await get_video_data_and_details(user_url)
        if not video_data:
            await update.message.reply_text("❌ Error: Could not retrieve video data.")
            return

        # 2. AI CAPTION WITH @TAGGING
        # We pass the owner_handle directly to the AI to ensure accurate tagging
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{
                "role": "user",
                "content": f"Write a viral Gen Z caption for a Reel. The original creator is @{owner_handle}. Use exactly 3 hashtags. Give credit by tagging @{owner_handle} clearly."
            }]
        )
        ai_caption = completion.choices[0].message.content

        # 3. INITIALIZE RESUMABLE SESSION
        init_res = requests.post(f"https://graph.facebook.com/v19.0/{INSTAGRAM_BUSINESS_ID}/media", data={
            "media_type": "REELS",
            "upload_type": "resumable",
            "caption": ai_caption,
            "access_token": INSTAGRAM_ACCESS_TOKEN
        }).json()

        container_id = init_res.get('id')
        if not container_id:
            await update.message.reply_text(f"❌ Session Fail: {init_res.get('error', {}).get('message')}")
            return

        # 4. UPLOAD VIDEO BYTES
        upload_url = f"https://rupload.facebook.com/ig-api-upload/v19.0/{container_id}"
        headers = {
            "Authorization": f"OAuth {INSTAGRAM_ACCESS_TOKEN}",
            "offset": "0",
            "file_size": str(len(video_data))
        }
        requests.post(upload_url, headers=headers, data=video_data)

        # 5. FINAL PUBLISH
        await update.message.reply_text(f"⏳ Uploaded! Tagging @{owner_handle} and pushing to grid...")
        await asyncio.sleep(40)

        publish_res = requests.post(f"https://graph.facebook.com/v19.0/{INSTAGRAM_BUSINESS_ID}/media_publish", data={
            "creation_id": container_id,
            "share_to_feed": "true",
            "access_token": INSTAGRAM_ACCESS_TOKEN
        }).json()

        if "id" in publish_res:
            await update.message.reply_text(f"✅ SUCCESS! Posted to @solevaaaaa.\n\nCaption used:\n{ai_caption}")
        else:
            await update.message.reply_text(f"⚠️ Meta Status: {publish_res.get('error', {}).get('message')}")

    except Exception as e:
        await update.message.reply_text(f"⚠️ Bot Error: {str(e)}")

def main():
    print("Bot is LIVE with Resumable Upload & Auto-Tagging...")
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_reel))
    app.run_polling()

if __name__ == "__main__":
    main()