import asyncio
import os
from telethon import TelegramClient

# بررسی متغیرهای محیطی
def check_env_vars():
    required_vars = ['TELEGRAM_API_ID', 'TELEGRAM_API_HASH', 'TELEGRAM_BOT_TOKEN']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"متغیرهای محیطی زیر موجود نیستند: {', '.join(missing_vars)}")

check_env_vars()

# متغیرها
api_id = int(os.getenv('TELEGRAM_API_ID'))
api_hash = os.getenv('TELEGRAM_API_HASH')
bot_token = os.getenv('TELEGRAM_BOT_TOKEN')

async def main():
    print(f"استفاده از bot_token: {bot_token[:5]}...")
    client = TelegramClient('test_session', api_id, api_hash)
    try:
        await client.start(bot_token=bot_token)
        print("اتصال با موفقیت برقرار شد!")
    except Exception as e:
        print(f"خطا در اتصال: {str(e)}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())