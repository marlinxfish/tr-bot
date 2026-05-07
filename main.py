import os
import random
import string
import time
import datetime
from faker import Faker
import requests
from concurrent.futures import ThreadPoolExecutor

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
        print("Tidak ada proxy di file proxy.txt. Menggunakan direct connection.")
        return None

    random_proxy = random.choice(proxies)
    formatted_proxy = format_proxy_string(random_proxy)
    print(f"\nProxy acak yang dipilih: {random_proxy}")
    return formatted_proxy

def write_result(email, password, api_key):
    file_exists = os.path.exists(KEYS_FILE)
    mode = 'a' if file_exists else 'w'
    
    with open(KEYS_FILE, mode) as f:
        f.write(f"{api_key}\n")
            
    with open(USERS_FILE, 'a') as f:
        f.write(f"{email}:{password}:{api_key}\n")
    
    print(f"Berhasil menyimpan detail akun untuk {email}")

def generate_random_name():
    return fake.name()

def generate_random_email(name):
    domains = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "mail.xyz", "pro.com", "me.com", "web.net"]
    clean_name = name.lower().replace(" ", "").replace(".", "").replace("-", "")
    random_num = random.randint(10, 99999)
    domain = random.choice(domains)
    return f"{clean_name}{random_num}@{domain}"

def run_automation(is_headless):
    print("\n--- Memulai Bot Pembuat Akun TheRouter.ai ---")
    
    best_proxy = get_random_proxy()
    
    proxy_config = None
    if best_proxy:
        proxy_config = best_proxy
        
    name = generate_random_name()
    email = generate_random_email(name)
    password = "Babi123456789*"
    
    print(f"Target Akun: {name} | {email}")

    try:
        # Camoufox secara default lebih stealth daripada Playwright standar.
        # Menambahkan geoip=True akan menyamakan timezone & koordinat browser dengan lokasi proxy!
        with Camoufox(
            headless=is_headless,
            proxy=proxy_config,
            geoip=True if best_proxy else False 
        ) as browser:
            page = browser.new_page()
            
            print(f"Membuka website {BASE_DOMAIN}...")
            page.goto(f"https://{BASE_DOMAIN}/")
            page.wait_for_timeout(2000)
            
            page.get_by_role("link", name="Dashboard →").click()
            page.wait_for_timeout(2000)
            
            page.get_by_role("link", name="Create account").click()
            page.wait_for_timeout(2000)
            
            print("Mengisi formulir pendaftaran...")
            page.get_by_role("textbox", name="Name (optional)").click()
            page.get_by_role("textbox", name="Name (optional)").fill(name)
            page.get_by_role("textbox", name="Email").fill(email)
            page.get_by_role("textbox", name="Password", exact=True).fill(password)
            page.get_by_role("textbox", name="Confirm Password").fill(password)
            
            page.get_by_role("button", name="Create Account").click()
            
            print("Menunggu pembuatan akun selesai (delay 10 detik)...")
            page.wait_for_timeout(10000)
            
            print("Membuka halaman login...")
            page.goto(f"https://dashboard.{BASE_DOMAIN}/login")
            page.wait_for_timeout(2000)
            
            print("Proses Login...")
            page.get_by_role("textbox", name="Email").click()
            page.get_by_role("textbox", name="Email").fill(email)
            page.get_by_role("textbox", name="Email").press("Tab")
            
            page.get_by_role("textbox", name="Password").click()
            page.get_by_role("textbox", name="Password").fill(password)
            page.get_by_role("textbox", name="Password").press("Tab")
            
            page.wait_for_timeout(1000)
            page.get_by_role("button", name="Sign In").click()
            
            print("Menunggu proses login (delay 5 detik)...")
            page.wait_for_timeout(5000)
            
            print("Membuka dashboard activity...")
            page.goto(f"https://dashboard.{BASE_DOMAIN}/activity")
            page.wait_for_timeout(2000)
            
            print("Membuat API Key baru...")
            page.get_by_role("link", name="Create API Key").click()
            
            key_name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
            page.get_by_role("textbox", name="Production API").fill(key_name)
            page.get_by_role("combobox").select_option("monthly")
            page.get_by_role("button", name="Create Key").click()
            
            print("Menyalin API Key...")
            page.wait_for_selector("text=/sk-.*/", timeout=10000)
            
            api_key_element = page.locator("text=/sk-.*/").first
            api_key = api_key_element.inner_text().strip()
            
            print(f"API Key berhasil didapatkan: {api_key}")
            
            write_result(email, password, api_key)
            
            print("Proses selesai.")
            
    except Exception as e:
        print(f"Terjadi error: {e}")

if __name__ == "__main__":
    pilihan = input("Jalankan bot secara Headless (sembunyikan browser)? [y/n]: ").strip().lower()
    is_headless = pilihan == 'y'

    if os.path.exists(KEYS_FILE):
        with open(KEYS_FILE, 'a') as f:
            f.write(f"\n\n--- Dibuat pada: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")
            
    run_automation(is_headless)
