import os

def repair_proxies():
    input_file = "proxy-repair.txt"
    output_file = "proxy.txt"

    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' tidak ditemukan!")
        print("Silakan buat file tersebut dan masukkan proxy dengan format username:password@ip:port")
        return

    print("=== Alat Perbaikan Format Proxy ===")
    print("Contoh input dari proxy-repair.txt: username:password@ip:port")
    print("Format output ke proxy.txt : protocol://ip:port:username:password\n")
    
    protocol = input("Masukkan protokol proxy yang digunakan (contoh: http, socks4, socks5): ").strip().lower()
    if not protocol:
        protocol = "http"
        print("Tidak ada input, menggunakan default: http")

    valid_proxies = []
    error_count = 0

    with open(input_file, 'r') as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        if not line:
            continue

        try:
            # Parsing format: username:password@ip:port
            if "@" in line:
                auth_part, ip_port_part = line.split("@", 1)
                
                # Cek apakah format auth benar
                if ":" in auth_part and ":" in ip_port_part:
                    username, password = auth_part.split(":", 1)
                    ip, port = ip_port_part.split(":", 1)
                    
                    # Konversi ke format script utama kita (format yang didukung format_proxy_string)
                    # Bisa disimpan sebagai protocol://ip:port:username:password
                    formatted_proxy = f"{protocol}://{ip}:{port}:{username}:{password}"
                    valid_proxies.append(formatted_proxy)
                else:
                    error_count += 1
            else:
                # Jika kebetulan formatnya ip:port (tanpa password)
                if ":" in line:
                    ip, port = line.split(":", 1)
                    formatted_proxy = f"{protocol}://{ip}:{port}"
                    valid_proxies.append(formatted_proxy)
                else:
                    error_count += 1
        except Exception as e:
            error_count += 1

    if valid_proxies:
        with open(output_file, 'w') as f:
            for proxy in valid_proxies:
                f.write(proxy + "\n")
        
        print(f"\nBerhasil! {len(valid_proxies)} proxy telah diperbaiki dan disimpan ke {output_file}")
        if error_count > 0:
            print(f"Peringatan: Ada {error_count} baris yang diabaikan karena formatnya salah/tidak sesuai.")
    else:
        print("\nTidak ada proxy yang berhasil diproses. Pastikan format di proxy-repair.txt benar.")

if __name__ == "__main__":
    repair_proxies()
