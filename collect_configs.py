import asyncio
import os
import re
import subprocess
import logging
from functools import lru_cache
from telethon import TelegramClient
from telethon.errors import FloodWaitError, InviteHashExpiredError, UserNotMutualContactError
from telethon.tl.functions.channels import JoinChannelRequest
import pycountry
from ip2geotools.databases.noncommercial import DbIpCity
import urllib.parse
import ipaddress

# تنظیم لوجینگ
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# بررسی متغیرهای محیطی
def check_env_vars():
    required_vars = ['TELEGRAM_API_ID', 'TELEGRAM_API_HASH', 'TELEGRAM_PHONE', 'V2RAY_TOKEN']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"متغیرهای محیطی زیر موجود نیستند: {', '.join(missing_vars)}")

check_env_vars()

# متغیرهای محیطی
api_id = int(os.getenv('TELEGRAM_API_ID'))
api_hash = os.getenv('TELEGRAM_API_HASH')
phone_number = os.getenv('TELEGRAM_PHONE')
v2ray_token = os.getenv('V2RAY_TOKEN')
config_file_path = os.getenv('CONFIG_FILE_PATH', 'vless_hysteria2_configs.txt')

# لیست لینک‌های کانال‌های تلگرام
channels = [
    "https://t.me/s/sinavm",
    "https://t.me/another_channel_link",
    "https://t.me/joinchat/SOME_INVITE_HASH",
    # لینک‌های واقعی کانال‌ها رو اینجا اضافه کن
]

# لیست کشورهای مجاز
allowed_countries = [
    'United States', 'Russia', 'Australia', 'United Kingdom', 'Germany',
    'Sweden', 'Finland', 'Estonia', 'Denmark', 'Luxembourg', 'Japan',
    'Singapore', 'Mexico', 'Brazil'
]

# پورت‌های ممنوعه
forbidden_ports = ['80', '8080', '8181', '3128']

# تابع بررسی وجود متن فارسی
def contains_persian(text):
    persian_pattern = re.compile(r'[\u0600-\u06FF]')
    return bool(persian_pattern.search(text))

# تابع استخراج IP و پورت
def extract_ip_port(config):
    try:
        parsed = urllib.parse.urlparse(config)
        host_port = parsed.netloc
        if '[' in host_port and ']' in host_port:
            ip = host_port.split(']')[0].strip('[')
            port = host_port.split(':')[-1] if ':' in host_port else None
        else:
            parts = host_port.split(':')
            ip = parts[0]
            port = parts[1] if len(parts) > 1 else None
        ipaddress.ip_address(ip)
        return ip, port
    except (ValueError, IndexError):
        return None, None

# تابع بررسی پینگ
async def test_ping(ip):
    try:
        cmd = ['ping', '-c', '4', '-W', '2', ip]
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        if process.returncode == 0:
            logger.info(f"پینگ موفق برای IP: {ip}")
            return True
        else:
            logger.warning(f"پینگ ناموفق برای IP: {ip}")
            return False
    except Exception as e:
        logger.error(f"خطا در بررسی پینگ برای IP {ip}: {str(e)}")
        return False

# تابع دریافت کشور سرور
@lru_cache(maxsize=1000)
def get_country(ip):
    if not re.match(r'^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|\[?([0-9a-fA-F:]+)\]?)$', ip):
        return None
    try:
        response = DbIpCity.get(ip, api_key='free')
        country_code = response.country
        if country_code == 'ZZ':
            return 'Unknown'
        return pycountry.countries.get(alpha_2=country_code).name
    except Exception:
        return None

# تابع عضویت در کانال‌ها
async def join_channels(channel_list, api_id, api_hash, phone_number):
    logger.info("تلاش برای عضویت در کانال‌های تلگرام...")
    async with TelegramClient('session_join', api_id, api_hash) as client:
        try:
            await client.start(phone=phone_number)
        except EOFError:
            logger.error("نیاز به تأیید ورود تلگرام. لطفاً اسکریپت را به صورت محلی اجرا کنید و کد تأیید را وارد کنید.")
            raise
        except Exception as e:
            logger.error(f"خطا در اتصال به تلگرام: {str(e)}")
            raise
        for channel_link in channel_list:
            try:
                match = re.search(r't.me/(?:s/|joinchat/|\+)?([a-zA-Z0-9_]+)', channel_link)
                if not match:
                    logger.warning(f"فرمت لینک کانال نامعتبر: {channel_link}")
                    continue
                channel_entity = match.group(1)
                await client(JoinChannelRequest(channel_entity))
                logger.info(f"با موفقیت به کانال {channel_entity} پیوست")
            except (InviteHashExpiredError, UserNotMutualContactError) as e:
                logger.error(f"عدم امکان عضویت در {channel_link}: {str(e)}")
            except Exception as e:
                logger.error(f"خطا در عضویت در {channel_link}: {str(e)}")

# تابع جمع‌آوری کانفیگ‌ها با بررسی پینگ
async def collect_vless_hysteria2_configs():
    async with TelegramClient('session_collect', api_id, api_hash) as client:
        try:
            await client.start(phone=phone_number)
        except EOFError:
            logger.error("نیاز به تأیید ورود تلگرام. لطفاً اسکریپت را به صورت محلی اجرا کنید و کد تأیید را وارد کنید.")
            raise
        except Exception as e:
            logger.error(f"خطا در اتصال به تلگرام برای جمع‌آوری: {str(e)}")
            return []

        valid_configs = []

        for channel in channels:
            channel_identifier = channel.split('/')[-1]
            if channel_identifier.startswith('s/'):
                channel_identifier = channel_identifier[2:]
            elif 'joinchat' in channel:
                match = re.search(r'joinchat/([a-zA-Z0-9_]+)', channel)
                if match:
                    channel_identifier = match.group(1)
                else:
                    logger.warning(f"شناسه معتبر برای جمع‌آوری از لینک دعوت یافت نشد: {channel}")
                    continue

            try:
                logger.info(f"دریافت پیام‌ها از کانال: {channel_identifier}")
                async for message in client.iter_messages(channel_identifier, limit=200):
                    if not message or not message.text:
                        continue
                    configs = re.findall(r'(vless://[^\s]+|hysteria2://[^\s]+)', message.text)
                    for config in configs:
                        if contains_persian(config):
                            continue
                        ip, port = extract_ip_port(config)
                        if not ip:
                            continue
                        if port and port in forbidden_ports:
                            continue
                        if not await test_ping(ip):
                            continue
                        country = get_country(ip)
                        if country is None or country == 'Unknown':
                            valid_configs.append(config)
                        elif country in allowed_countries:
                            valid_configs.append(config)
                    await asyncio.sleep(0.1)
            except FloodWaitError as e:
                logger.warning(f"محدودیت نرخ تلگرام، منتظر {e.seconds} ثانیه")
                await asyncio.sleep(e.seconds)
            except Exception as e:
                logger.error(f"خطا در پردازش کانال {channel_identifier}: {str(e)}")

        return valid_configs

# تابع ذخیره کانفیگ‌ها
def save_configs_to_file(configs, file_path=config_file_path):
    try:
        unique_configs = list(set(config.strip() for config in configs))
        logger.info(f"{len(configs) - len(unique_configs)} کانفیگ تکراری حذف شد")

        try:
            with open(file_path, 'r') as f:
                existing_configs = f.read().splitlines()
        except FileNotFoundError:
            existing_configs = []
            logger.info(f"فایل {file_path} یافت نشد. فایل جدید ایجاد می‌شود")

        if sorted(unique_configs) != sorted(existing_configs):
            with open(file_path, 'w') as f:
                for config in unique_configs:
                    f.write(config + '\n')
            logger.info(f"{len(unique_configs)} کانفیگ معتبر در {file_path} نوشته شد")

            subprocess.run(['git', 'config', '--global', 'user.name', 'GitHub Action Bot'], check=True)
            subprocess.run(['git', 'config', '--global', 'user.email', 'bot@github.com'], check=True)
            result = subprocess.run(['git', 'diff', '--quiet', file_path], capture_output=True)
            if result.returncode != 0:
                subprocess.run(['git', 'add', file_path], check=True)
                subprocess.run(['git', 'commit', '-m', 'Update VLESS and Hysteria2 configs'], check=True)
                subprocess.run(['git', 'push', 'origin', 'main'], check=True)
                logger.info("کانفیگ‌ها با موفقیت کامیت و پوش شدند")
            else:
                logger.info("تغییری برای کامیت وجود ندارد")
        else:
            logger.info("محتوای فایل کانفیگ بدون تغییر است")
    except Exception as e:
        logger.error(f"خطا در ذخیره کانفیگ‌ها: {str(e)}")

# تابع اصلی
async def main():
    try:
        await join_channels(channels, api_id, api_hash, phone_number)
        configs = await collect_vless_hysteria2_configs()
        if configs:
            save_configs_to_file(configs)
        else:
            logger.warning("کانفیگ معتبری یافت نشد")
    except Exception as e:
        logger.error(f"خطا در اجرای اصلی: {str(e)}")
        raise

# اجرای اسکریپت
if __name__ == "__main__":
    asyncio.run(main())
