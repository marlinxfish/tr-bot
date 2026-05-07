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
    """
    Parses proxies that might be in the format: protocol://ip:port:user:pass
    and converts them to standard format: protocol://user:pass@ip:port
    Supports http, https, socks4, socks5.
    """
    proxy_str = proxy_str.strip()
    
    protocol = "http"
    if "://" in proxy_str:
        protocol, rest = proxy_str.split("://", 1)
    else:
        rest = proxy_str
        
    parts = rest.split(":")
    if len(parts) == 4:
        ip, port, user, pwd = parts
        return f"{protocol}://{user}:{pwd}@{ip}:{port}"
    elif len(parts) == 2:
        ip, port = parts
        return f"{protocol}://{ip}:{port}"
        
    return proxy_str

def check_proxy(original_proxy_url):
    """
    Checks the proxy latency and location.
    Returns (latency_ms, geo_info, formatted_proxy) if successful, None if failed.
    """
    formatted_proxy = format_proxy_string(original_proxy_url)
    proxies = {
        "http": formatted_proxy,
        "https": formatted_proxy,
    }
    start_time = time.time()
    try:
        response = requests.get("http://ip-api.com/json/", proxies=proxies, timeout=10)
        response.raise_for_status()
        latency = int((time.time() - start_time) * 1000)
        data = response.json()
        if data.get("status") == "success":
            location = f"{data.get('city')}, {data.get('country')}"
            return latency, location, formatted_proxy
        return latency, "Unknown Location", formatted_proxy
    except Exception as e:
        return None

def get_best_proxy():
    """Reads proxies from proxy.txt, checks them, and returns the fastest one."""
    if not os.path.exists(PROXY_FILE):
        return None

    with open(PROXY_FILE, 'r') as f:
        proxies = [line.strip() for line in f if line.strip()]

    if not proxies:
        return None

    print(f"Mengecek {len(proxies)} proxy...")
    
    valid_proxies = []
    
    with ThreadPoolExecutor(max_workers=min(10, len(proxies))) as executor:
        results = executor.map(check_proxy, proxies)
        
        for proxy, result in zip(proxies, results):
            if result:
                latency, location, formatted = result
                valid_proxies.append({
                    "original": proxy,
                    "formatted": formatted,
                    "latency": latency,
                    "location": location
                })
                print(f"[OK] {proxy} - {latency}ms - {location}")
            else:
                print(f"[FAIL] {proxy}")

    if not valid_proxies:
        print("Tidak ada proxy yang jalan. Menggunakan direct connection.")
        return None

    valid_proxies.sort(key=lambda x: x["latency"])
    best_proxy = valid_proxies[0]
    print(f"\nProxy tercepat yang dipilih: {best_proxy['original']} ({best_proxy['latency']}ms, {best_proxy['location']})")
    return best_proxy['formatted']

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
    
    best_proxy = get_best_proxy()
    
    proxy_config = None
    if best_proxy:
        proxy_config = {"server": best_proxy}
        
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
