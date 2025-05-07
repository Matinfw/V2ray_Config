import base64
import os
import logging
from telethon import TelegramClient

# تنظیم لاگینگ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('collect_configs.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# تابع بازسازی فایل سشن از Base64
def restore_session_file(session_base64, session_path):
    try:
        session_data = base64.b64decode(session_base64)
        with open(session_path, "wb") as f:
            f.write(session_data)
        logger.info(f"فایل سشن در {session_path} بازسازی شد.")
        return session_path
    except Exception as e:
        logger.error(f"خطا در بازسازی فایل سشن: {str(e)}")
        raise

# بررسی متغیرهای محیطی
required_vars = ['TELEGRAM_API_ID', 'TELEGRAM_API_HASH', 'TELEGRAM_PHONE', 'SESSION_COLLECT_BASE64', 'SESSION_JOIN_BASE64', 'SESSION_TYPE']
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    logger.error(f"متغیرهای محیطی زیر موجود نیستند: {', '.join(missing_vars)}")
    raise ValueError("متغیرهای محیطی گم‌شده.")

# خواندن متغیرها
api_id = int(os.getenv('TELEGRAM_API_ID'))
api_hash = os.getenv('TELEGRAM_API_HASH')
phone = os.getenv('TELEGRAM_PHONE')
session_type = os.getenv('SESSION_TYPE')  # 'collect' یا 'join'

# انتخاب سشن بر اساس SESSION_TYPE
if session_type == 'collect':
    session_base64 = os.getenv('SESSION_COLLECT_BASE64')
    session_path = "/tmp/session_collect.session"
elif session_type == 'join':
    session_base64 = os.getenv('SESSION_JOIN_BASE64')
    session_path = "/tmp/session_join.session"
else:
    logger.error(f"مقدار SESSION_TYPE نامعتبر است: {session_type}. باید 'collect' یا 'join' باشد.")
    raise ValueError("SESSION_TYPE نامعتبر.")

# بازسازی فایل سشن
session_file = restore_session_file(session_base64, session_path)

# اتصال به تلگرام
async def main():
    client = TelegramClient(session_file, api_id, api_hash)
    try:
        await client.start(phone=phone)
        logger.info(f"اتصال به تلگرام با سشن {session_type} برقرار شد.")
        # اینجا کد جمع‌آوری کانفیگ‌ها یا سایر عملیات ادامه می‌یابد
    finally:
        await client.disconnect()
        if os.path.exists(session_file):
            os.remove(session_file)
            logger.info(f"فایل سشن {session_file} حذف شد.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
