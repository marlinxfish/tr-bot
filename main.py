import os
import random
import string
import time
import datetime
from faker import Faker
import requests
from concurrent.futures import ThreadPoolExecutor

os.system("color")  # Enable ANSI colors for Windows

def log_info(msg):
    now = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[\033[94m{now}\033[0m] [\033[96mINFO\033[0m] {msg}")

def log_success(msg):
    now = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[\033[94m{now}\033[0m] [\033[92mSUCCESS\033[0m] {msg}")

def log_error(msg):
    now = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[\033[94m{now}\033[0m] [\033[91mERROR\033[0m] {msg}")

def log_warning(msg):
    now = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[\033[94m{now}\033[0m] [\033[93mWARNING\033[0m] {msg}")

# Import Camoufox
from camoufox.sync_api import Camoufox

from dotenv import load_dotenv
load_dotenv()

BASE_DOMAIN = os.getenv("BASE_DOMAIN", "therouter.ai")

fake = Faker()

PROXY_FILE = "proxy.txt"
RESULT_DIR = "result"
KEYS_FILE = os.path.join(RESULT_DIR, "keys.txt")
USERS_FILE = os.path.join(RESULT_DIR, "user.txt")

# Ensure result directory exists
os.makedirs(RESULT_DIR, exist_ok=True)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_USER_ID = os.getenv("TELEGRAM_USER_ID", "")

try:
    import telebot
    bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN) if TELEGRAM_BOT_TOKEN else None
except ImportError:
    bot = None

if bot:
    @bot.message_handler(commands=['total', 'jumlah'])
    def handle_total(message):
        if str(message.chat.id) != str(TELEGRAM_USER_ID):
            return
        
        total = 0
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, 'r') as f:
                total = sum(1 for line in f if line.strip())
        
        bot.reply_to(message, f"✅ Total akun yang berhasil dibuat: {total} akun.")

    def run_telegram_bot():
        try:
            bot.infinity_polling()
        except Exception as e:
            pass

def format_proxy_string(proxy_str):
    proxy_str = proxy_str.strip()
    
    protocol = "http"
    if "://" in proxy_str:
        protocol, rest = proxy_str.split("://", 1)
    else:
        rest = proxy_str
        
    parts = rest.split(":")
    if len(parts) == 4:
        ip, port, user, pwd = parts
        return {
            "server": f"{protocol}://{ip}:{port}",
            "username": user,
            "password": pwd
        }
    elif len(parts) == 2:
        ip, port = parts
        return {"server": f"{protocol}://{ip}:{port}"}
        
    return {"server": proxy_str}

def get_random_proxy():
    """Reads proxies from proxy.txt and returns one random proxy without checking."""
    if not os.path.exists(PROXY_FILE):
        return None

    with open(PROXY_FILE, 'r') as f:
        proxies = [line.strip() for line in f if line.strip()]

    if not proxies:
        log_warning("Tidak ada proxy di file proxy.txt. Menggunakan direct connection.")
        return None

    random_proxy = random.choice(proxies)
    formatted_proxy = format_proxy_string(random_proxy)
    log_info(f"Proxy acak yang dipilih: {random_proxy}")
    return formatted_proxy

def write_result(email, password, api_key):
    days = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
    now = datetime.datetime.now()
    nama_hari = days[now.weekday()]
    tanggal = now.strftime("%Y-%m-%d")
    header_str = f"{nama_hari} {tanggal}"
    
    file_exists = os.path.exists(KEYS_FILE)
    mode = 'a' if file_exists else 'w'
    
    needs_header = True
    if file_exists:
        with open(KEYS_FILE, 'r') as f:
            if header_str in f.read():
                needs_header = False
                
    with open(KEYS_FILE, mode) as f:
        if needs_header:
            f.write(f"\n\n{header_str}\n")
        f.write(f"{api_key}\n")
            
    with open(USERS_FILE, 'a') as f:
        f.write(f"{email}:{password}:{api_key}\n")
    
    log_success(f"Berhasil menyimpan detail akun untuk {email}")

def generate_random_name():
    return fake.name()

def generate_random_email(name):
    domains = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "mail.xyz", "pro.com", "me.com", "web.net"]
    clean_name = name.lower().replace(" ", "").replace(".", "").replace("-", "")
    random_num = random.randint(10, 99999)
    domain = random.choice(domains)
    return f"{clean_name}{random_num}@{domain}"

def run_automation(is_headless, akun_dibuat=0):
    best_proxy = get_random_proxy()
    
    proxy_config = None
    if best_proxy:
        proxy_config = best_proxy
        
    name = generate_random_name()
    email = generate_random_email(name)
    password = "Babi123456789*"
    
    log_info(f"Target Akun: {name} | {email}")

    account_created = False
    try:
        # Camoufox secara default lebih stealth daripada Playwright standar.
        # Menambahkan geoip=True akan menyamakan timezone & koordinat browser dengan lokasi proxy!
        with Camoufox(
            headless=is_headless,
            proxy=proxy_config,
            geoip=True if best_proxy else False 
        ) as browser:
            page = browser.new_page()
            
            log_info(f"Membuka website {BASE_DOMAIN}...")
            page.goto(f"https://{BASE_DOMAIN}/")
            page.wait_for_timeout(2000)
            
            page.get_by_role("link", name="Dashboard →").click()
            page.wait_for_timeout(2000)
            
            page.get_by_role("link", name="Create account").click()
            page.wait_for_timeout(2000)
            
            log_info("Mengisi formulir pendaftaran...")
            page.get_by_role("textbox", name="Name (optional)").click()
            page.get_by_role("textbox", name="Name (optional)").fill(name)
            page.get_by_role("textbox", name="Email").fill(email)
            page.get_by_role("textbox", name="Password", exact=True).fill(password)
            page.get_by_role("textbox", name="Confirm Password").fill(password)
            
            page.get_by_role("button", name="Create Account").click()
            
            log_info("Menunggu pembuatan akun selesai (delay 10 detik)...")
            page.wait_for_timeout(10000)
            account_created = True
            
            log_info("Membuka halaman login...")
            page.goto(f"https://dashboard.{BASE_DOMAIN}/login")
            page.wait_for_timeout(2000)
            
            log_info("Proses Login...")
            page.get_by_role("textbox", name="Email").click()
            page.get_by_role("textbox", name="Email").fill(email)
            page.get_by_role("textbox", name="Email").press("Tab")
            
            page.get_by_role("textbox", name="Password").click()
            page.get_by_role("textbox", name="Password").fill(password)
            page.get_by_role("textbox", name="Password").press("Tab")
            
            page.wait_for_timeout(1000)
            page.get_by_role("button", name="Sign In").click()
            
            log_info("Menunggu proses login (delay 5 detik)...")
            page.wait_for_timeout(5000)
            
            log_info("Membuka dashboard activity...")
            page.goto(f"https://dashboard.{BASE_DOMAIN}/activity")
            page.wait_for_timeout(2000)
            
            log_info("Membuat API Key baru...")
            page.get_by_role("link", name="Create API Key").click()
            
            key_name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
            page.get_by_role("textbox", name="Production API").fill(key_name)
            page.get_by_role("combobox").select_option("monthly")
            page.get_by_role("button", name="Create Key").click()
            
            log_info("Menyalin API Key...")
            page.wait_for_selector("text=/sk-.*/", timeout=10000)
            
            api_key_element = page.locator("text=/sk-.*/").first
            api_key = api_key_element.inner_text().strip()
            
            log_success(f"API Key berhasil didapatkan: {api_key}")
            
            write_result(email, password, api_key)
            
            if bot and TELEGRAM_USER_ID:
                try:
                    bot.send_message(TELEGRAM_USER_ID, f"✅ *Akun Berhasil Dibuat!*\n\n📧 Email: `{email}`\n\n_Akun ke-{akun_dibuat}_", parse_mode="Markdown")
                except Exception:
                    pass
            
            log_success("Proses selesai.")
            
    except Exception as e:
        log_error(f"Terjadi error pada browser: {e}")
        if account_created:
            reg_file = os.path.join(RESULT_DIR, "register-only.txt")
            with open(reg_file, "a") as f:
                f.write(f"{email}:{password}\n")
            log_warning(f"Akun sudah terdaftar tapi gagal ambil key. Tersimpan di register-only.txt")
            if bot and TELEGRAM_USER_ID:
                try:
                    bot.send_message(TELEGRAM_USER_ID, f"⚠️ *Akun Terdaftar Tanpa Key*\n\n📧 Email: `{email}`\n❌ Gagal login atau ambil key.\n_Tersimpan di register-only.txt_", parse_mode="Markdown")
                except Exception:
                    pass
        # Jangan stop, biarkan fungsi return agar loop berlanjut

if __name__ == "__main__":
    os.system('cls' if os.name == 'nt' else 'clear')
    print("\n\033[96m=====================================================")
    print("      Bot Auto-Create Account TheRouter.ai")
    print("=====================================================\033[0m\n")
    
    pilihan = input("Jalankan bot secara Headless (sembunyikan browser)? [y/n]: ").strip().lower()
    is_headless = pilihan == 'y'


    if bot:
        import threading
        tg_thread = threading.Thread(target=run_telegram_bot, daemon=True)
        tg_thread.start()
        log_info("Telegram bot listener aktif.")

    log_info("Memulai loop pembuatan akun tanpa henti. Tekan Ctrl+C untuk berhenti.")
    
    akun_dibuat = 0
    while True:
        try:
            akun_dibuat += 1
            print(f"\n\033[93m>>> --- Memulai Proses Untuk Akun Ke-{akun_dibuat} ---\033[0m")
            run_automation(is_headless, akun_dibuat)
            log_info("Jeda 3 detik sebelum lanjut ke akun berikutnya...")
            time.sleep(3)
        except KeyboardInterrupt:
            print("\n")
            log_warning("Bot dihentikan secara manual oleh pengguna (Ctrl+C).")
            break
        except Exception as e:
            log_error(f"Terjadi error sistem tak terduga: {e}")
            log_info("Melanjutkan ke pembuatan akun berikutnya...")
            time.sleep(3)
