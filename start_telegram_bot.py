#!/usr/bin/env python3
"""
Start Telegram Bot for KeLiva
This script sets up the webhook and starts listening for messages
"""

import os
import sys
import asyncio
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv('backend/.env')

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_WEBHOOK_URL = os.getenv('TELEGRAM_WEBHOOK_URL')

# For local development, use ngrok or similar
# For production, use your actual domain
LOCAL_WEBHOOK_URL = "http://localhost:8000/api/telegram/webhook"


async def set_webhook(webhook_url: str):
    """Set the webhook URL for the Telegram bot"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json={"url": webhook_url})
            result = response.json()
            
            if result.get('ok'):
                print(f"✅ Webhook set successfully!")
                print(f"   URL: {webhook_url}")
                return True
            else:
                print(f"❌ Failed to set webhook: {result.get('description')}")
                return False
        except Exception as e:
            print(f"❌ Error setting webhook: {e}")
            return False


async def get_webhook_info():
    """Get current webhook information"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getWebhookInfo"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            result = response.json()
            
            if result.get('ok'):
                info = result.get('result', {})
                print("\n📊 Current Webhook Info:")
                print(f"   URL: {info.get('url', 'Not set')}")
                print(f"   Pending updates: {info.get('pending_update_count', 0)}")
                if info.get('last_error_message'):
                    print(f"   Last error: {info.get('last_error_message')}")
                return info
            else:
                print(f"❌ Failed to get webhook info: {result.get('description')}")
                return None
        except Exception as e:
            print(f"❌ Error getting webhook info: {e}")
            return None


async def delete_webhook():
    """Delete the current webhook"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteWebhook"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url)
            result = response.json()
            
            if result.get('ok'):
                print("✅ Webhook deleted successfully!")
                return True
            else:
                print(f"❌ Failed to delete webhook: {result.get('description')}")
                return False
        except Exception as e:
            print(f"❌ Error deleting webhook: {e}")
            return False


async def get_bot_info():
    """Get bot information"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            result = response.json()
            
            if result.get('ok'):
                bot = result.get('result', {})
                print("\n🤖 Bot Information:")
                print(f"   Name: {bot.get('first_name')}")
                print(f"   Username: @{bot.get('username')}")
                print(f"   ID: {bot.get('id')}")
                return bot
            else:
                print(f"❌ Failed to get bot info: {result.get('description')}")
                return None
        except Exception as e:
            print(f"❌ Error getting bot info: {e}")
            return None


async def main():
    """Main function"""
    print("=" * 60)
    print("🚀 KeLiva Telegram Bot Setup")
    print("=" * 60)
    
    if not TELEGRAM_BOT_TOKEN:
        print("❌ Error: TELEGRAM_BOT_TOKEN not found in .env file")
        print("   Please add your bot token from @BotFather")
        sys.exit(1)
    
    # Get bot info
    bot_info = await get_bot_info()
    if not bot_info:
        print("\n❌ Failed to connect to Telegram API")
        print("   Please check your TELEGRAM_BOT_TOKEN")
        sys.exit(1)
    
    # Get current webhook info
    await get_webhook_info()
    
    print("\n" + "=" * 60)
    print("Choose an option:")
    print("=" * 60)
    print("1. Set webhook for LOCAL development (requires ngrok)")
    print("2. Set webhook for PRODUCTION (use .env URL)")
    print("3. Delete webhook (use polling instead)")
    print("4. Just show current status")
    print("5. Exit")
    print("=" * 60)
    
    choice = input("\nEnter your choice (1-5): ").strip()
    
    if choice == '1':
        print("\n⚠️  For local development, you need ngrok or similar tool")
        print("   1. Install ngrok: https://ngrok.com/download")
        print("   2. Run: ngrok http 8000")
        print("   3. Copy the HTTPS URL (e.g., https://abc123.ngrok.io)")
        ngrok_url = input("\nEnter your ngrok HTTPS URL (or press Enter to skip): ").strip()
        
        if ngrok_url:
            webhook_url = f"{ngrok_url}/api/telegram/webhook"
            await set_webhook(webhook_url)
            print("\n✅ Setup complete!")
            print(f"\n📱 Now you can message your bot: @{bot_info.get('username')}")
            print("   Make sure your backend is running on port 8000")
        else:
            print("❌ Cancelled")
    
    elif choice == '2':
        if TELEGRAM_WEBHOOK_URL and TELEGRAM_WEBHOOK_URL != "https://your-app.onrender.com/api/telegram/webhook":
            await set_webhook(TELEGRAM_WEBHOOK_URL)
            print("\n✅ Setup complete!")
            print(f"\n📱 Now you can message your bot: @{bot_info.get('username')}")
        else:
            print("❌ Please set TELEGRAM_WEBHOOK_URL in your .env file")
            print("   Example: https://your-app.onrender.com/api/telegram/webhook")
    
    elif choice == '3':
        await delete_webhook()
        print("\n✅ Webhook deleted!")
        print("   Note: Polling mode is not implemented in this version")
        print("   You need to use webhook mode for the bot to work")
    
    elif choice == '4':
        print("\n✅ Status shown above")
    
    else:
        print("\n👋 Goodbye!")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
