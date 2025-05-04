import asyncio
import os
import re
import time
from telethon import TelegramClient
from telethon.tl.functions.channels import JoinChannelRequest
import pycountry
from ip2geotools.databases.noncommercial import DbIpCity
import urllib.parse
import subprocess

# بررسی متغیرهای محیطی
def check_env_vars():
    required_vars = ['TELEGRAM_API_ID', 'TELEGRAM_API_HASH', 'TELEGRAM_PHONE', 'V2RAY_TOKEN']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"متغیرهای محیطی زیر موجود نیستند: {', '.join(missing_vars)}")

check_env_vars()

# متغیرهای محیطی از GitHub Secrets
api_id = int(os.getenv('TELEGRAM_API_ID'))
api_hash = os.getenv('TELEGRAM_API_HASH')
phone_number = os.getenv('TELEGRAM_PHONE')
v2ray_token = os.getenv('V2RAY_TOKEN')

# لیست لینک‌های کانال‌های تلگرام
channels = [
    "https://t.me/s/An0nymousTeam",
    "https://t.me/s/VlessConfig",
    "https://t.me/s/V2rayng52",
    "https://t.me/s/NT_Safe",
    "https://t.me/s/ripaojiedian",
    "https://t.me/s/v2rayng2i",
    "https://t.me/s/WangCai2",
    "https://t.me/s/proxy_kafee",
    "https://t.me/s/v2raymeliy",
    "https://t.me/s/v2raytun",
    "https://t.me/s/vlesskeys",
    "https://t.me/s/Hysteriay",
    "https://t.me/s/PrivateVPNs",
    "https://t.me/s/Hysteria000",
    "https://t.me/s/V2rayng_Vpn403",
    "https://t.me/s/FASTSHOVPN",
    "https://t.me/s/outlineOpenKey"
    "https://t.me/s/free4allVPN"
    "https://t.me/s/V2rayNG3"
    "https://t.me/s/DailyV2RY"
    "https://t.me/s/VlessConfig"
    "https://t.me/s/V2ray_Collector"
    "https://t.me/s/MTConfig"
    # لینک‌های دیگر را اضافه کنید
]

# لیست کشورهای مجاز
allowed_countries = [
    'United States', 'Russia', 'Australia', 'United Kingdom', 'Germany',
    'Sweden', 'Finland', 'Estonia', 'Denmark', 'Luxembourg', 'Japan',
    'Singapore', 'Mexico', 'Brazil'
]

# پورت‌های ممنوعه
forbidden_ports = ['80', '8080', '8880', '8181', '3128']

# تابع استخراج IP و پورت از کانفیگ‌های VLESS یا Hysteria2
def extract_ip_port(config):
    try:
        parsed = urllib.parse.urlparse(config)
        if parsed.scheme == 'hysteria2':
            host_port = parsed.netloc
            if '[' in host_port and ']' in host_port:  # مدیریت IPv6
                match = re.match(r'\[([0-9a-fA-F:]+)\](?::(\d+))?', host_port)
                if match:
                    ip = match.group(1)
                    port = match.group(2)
                else:
                    ip = None
                    port = None
            else:  # مدیریت IPv4 یا نام میزبان
                parts = host_port.split(':')
                ip = parts[0]
                port = parts[1] if len(parts) > 1 else None
        else:  # فرض VLESS یا مشابه
            ip_port = parsed.netloc.split(':')
            ip = ip_port[0]
            port = ip_port[1] if len(ip_port) > 1 else None
        return ip, port
    except Exception as e:
        return None, None

# تابع دریافت کشور سرور
def get_country(ip):
    if not re.match(r'^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|\[?([0-9a-fA-F:]+)\]?)$', ip):
        return None
    try:
        response = DbIpCity.get(ip, api_key='free')
        country_code = response.country
        if country_code == 'ZZ':
            return 'Unknown'
        try:
            country_name = pycountry.countries.get(alpha_2=country_code).name
            return country_name
        except AttributeError:
            return country_code
    except Exception as e:
        return None

# تابع عضویت در کانال‌ها
async def join_channels(channel_list, api_id, api_hash, phone_number):
    print("تلاش برای عضویت در کانال‌های تلگرام...")
    try:
        async with TelegramClient('session_join', api_id, api_hash) as client:
            await client.start(phone=phone_number)
            for channel_link in channel_list:
                try:
                    print(f"تلاش برای پیوستن به: {channel_link}")
                    match = re.search(r't.me/(?:s/|joinchat/)?([a-zA-Z0-9_]+)', channel_link)
                    if match:
                        channel_entity = match.group(1)
                        await client(JoinChannelRequest(channel_entity))
                        print(f"با موفقیت به کانال/چت {channel_entity} پیوست.")
                    else:
                        print(f"فرمت لینک کانال نامعتبر: {channel_link}. رد می‌شود.")
                except Exception as e:
                    print(f"خطا در پیوستن به {channel_link}: {str(e)}")
            print("عملیات عضویت در کانال‌ها به پایان رسید.")
    except Exception as e:
        print(f"خطا در اتصال به تلگرام برای عملیات عضویت: {str(e)}")

# تابع جمع‌آوری کانفیگ‌ها از کانال‌های تلگرام
async def collect_vless_hysteria2_configs():
    async with TelegramClient('session_collect', api_id, api_hash) as client:
        try:
            await client.start(phone=phone_number)
        except Exception as e:
            print(f"خطا در اتصال به تلگرام برای جمع‌آوری: {str(e)}")
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
                    print(f"شناسه معتبر برای جمع‌آوری از لینک دعوت یافت نشد: {channel}. رد می‌شود.")
                    continue

            try:
                print(f"دریافت پیام‌ها از کانال: {channel_identifier}")
                async for message in client.iter_messages(channel_identifier, limit=200):
                    if not message or not message.text:
                        continue
                    configs = re.findall(r'(vless://[^\s]+|hysteria2://[^\s]+)', message.text)
                    if configs:
                        for config in configs:
                            ip, port = extract_ip_port(config)
                            if not ip:
                                continue
                            if port and port in forbidden_ports:
                                continue
                            country = get_country(ip)
                            if country is None or country == 'Unknown':
                                valid_configs.append(config)
                            elif country in allowed_countries:
                                valid_configs.append(config)
                    await asyncio.sleep(0.1)
            except Exception as e:
                print(f"خطا در پردازش کانال {channel_identifier}: {str(e)}")

        return valid_configs

# تابع ذخیره کانفیگ‌ها در فایل و کامیت به مخزن
def save_configs_to_file(configs, file_path='vless_hysteria2_configs.txt'):
    try:
        # خواندن محتوای موجود
        try:
            with open(file_path, 'r') as f:
                existing_configs = f.read().splitlines()
        except FileNotFoundError:
            existing_configs = []
            print(f"فایل {file_path} یافت نشد. یک فایل جدید ایجاد می‌شود.")

        # فیلتر کردن کانفیگ‌های منحصربه‌فرد
        seen = set()
        unique_configs = []
        for config in configs:
            if config not in seen:
                seen.add(config)
                unique_configs.append(config)
        
        print(f"{len(configs) - len(unique_configs)} کانفیگ تکراری حذف شد.")

        # مقایسه با محتوای موجود
        if sorted(unique_configs) != sorted(existing_configs):
            print(f"نوشتن {len(unique_configs)} کانفیگ معتبر در فایل {file_path}.")
            with open(file_path, 'w') as f:
                for config in unique_configs:
                    f.write(config + '\n')
            
            # عملیات Git برای کامیت و پوش
            try:
                subprocess.run(['git', 'config', '--global', 'user.name', 'GitHub Action Bot'], check=True)
                subprocess.run(['git', 'config', '--global', 'user.email', 'bot@github.com'], check=True)
                subprocess.run(['git', 'add', file_path], check=True)
                subprocess.run(['git', 'commit', '-m', 'Update VLESS and Hysteria2 configs'], check=True)
                repo_url = os.getenv('GITHUB_REPOSITORY')
                push_url = f"https://x-access-token:{v2ray_token}@github.com/{repo_url}.git"
                subprocess.run(['git', 'push', push_url], check=True)
                print("کانفیگ‌ها با موفقیت کامیت و پوش شدند.")
            except subprocess.CalledProcessError as e:
                print(f"خطا در عملیات Git: {str(e)}")
        else:
            print("محتوای فایل کانفیگ یکسان است. نیازی به نوشتن یا کامیت نیست.")
    except Exception as e:
        print(f"خطا در ذخیره کانفیگ‌ها در فایل: {str(e)}")

# تابع اصلی
async def main():
    try:
        await join_channels(channels, api_id, api_hash, phone_number)
        configs = await collect_vless_hysteria2_configs()
        if configs:
            save_configs_to_file(configs)
        else:
            print("پس از جمع‌آوری، کانفیگ معتبری یافت نشد. فایلی نوشته نمی‌شود.")
    except Exception as e:
        print(f"خطایی غیرمنتظره در طول اجرای اصلی رخ داد: {str(e)}")

# اجرای اسکریپت
if __name__ == "__main__":
    asyncio.run(main())
