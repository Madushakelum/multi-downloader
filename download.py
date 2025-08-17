import os
import requests
import time
from tqdm import tqdm
from colorama import Fore, Style, init
from concurrent.futures import ThreadPoolExecutor

# Initialize colorama
init(autoreset=True)

DOWNLOAD_DIR = "download"

def create_download_dir():
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)

def get_file_name(url):
    return url.split("/")[-1].split("?")[0]

def format_speed(bytes_per_sec):
    if bytes_per_sec > 1024 * 1024:
        return f"{bytes_per_sec / (1024*1024):.2f} MB/s"
    else:
        return f"{bytes_per_sec / 1024:.2f} KB/s"

def download_file(url, show_mode=True):
    local_filename = os.path.join(DOWNLOAD_DIR, get_file_name(url))
    temp_filename = local_filename + ".part"

    response = requests.head(url)
    if 'Content-Length' not in response.headers:
        print(Fore.RED + f"[ERROR] Can't fetch size for {url}")
        return

    total_size = int(response.headers.get('Content-Length', 0))
    resume_header = {}
    pos = 0

    if os.path.exists(temp_filename):
        pos = os.path.getsize(temp_filename)
        resume_header = {'Range': f'bytes={pos}-'}

    start_time = time.time()
    last_time = start_time
    downloaded = pos

    with requests.get(url, stream=True, headers=resume_header) as r:
        r.raise_for_status()
        mode = 'ab' if pos else 'wb'
        with open(temp_filename, mode) as f:
            bar_format = f"{Fore.GREEN}{{l_bar}}{{bar}}{Style.RESET_ALL} | {{n_fmt}}/{{total_fmt}}"
            with tqdm(total=total_size, initial=pos, unit='B', unit_scale=True,
                      desc=get_file_name(url), bar_format=bar_format, ncols=80) as pbar:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
                        downloaded += len(chunk)

                        # Speed calculation
                        current_time = time.time()
                        if current_time - last_time >= 1:
                            speed = format_speed((downloaded - pos) / (current_time - start_time))
                            pbar.set_postfix_str(f"Speed: {speed}")
                            last_time = current_time

    os.rename(temp_filename, local_filename)
    print(Fore.GREEN + f"\n[✔] Completed: {get_file_name(url)} ({round(total_size / (1024*1024), 2)} MB)")

def normal_mode():
    print(Fore.CYAN + Style.BRIGHT + "\n=== Normal Mode Selected ===")
    urls = []
    print(Fore.YELLOW + "Enter up to 20 URLs (press ENTER without typing to stop):\n")

    for i in range(1, 21):
        url = input(f"{Fore.MAGENTA}{i:02}. URL: {Style.RESET_ALL}").strip()
        if not url:
            break
        urls.append(url)

    if not urls:
        print(Fore.RED + "[!] No URLs provided. Exiting...")
        return

    print(Fore.CYAN + "\nStarting downloads...\n")
    for idx, url in enumerate(urls, start=1):
        print(Fore.YELLOW + f"\nDownloading {idx}/{len(urls)}: {url}")
        try:
            download_file(url)
        except Exception as e:
            print(Fore.RED + f"[ERROR] Failed to download {url}. Reason: {e}")

def parallel_mode():
    print(Fore.CYAN + Style.BRIGHT + "\n=== Parallel Mode Selected (3 Threads) ===")
    urls = []
    print(Fore.YELLOW + "Enter up to 20 URLs (press ENTER without typing to stop):\n")

    for i in range(1, 21):
        url = input(f"{Fore.MAGENTA}{i:02}. URL: {Style.RESET_ALL}").strip()
        if not url:
            break
        urls.append(url)

    if not urls:
        print(Fore.RED + "[!] No URLs provided. Exiting...")
        return

    print(Fore.CYAN + "\nStarting parallel downloads (3 at a time)...\n")

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(download_file, url, False) for url in urls]
        for future in futures:
            future.result()

def main():
    create_download_dir()
    print(Fore.CYAN + Style.BRIGHT + "=== Multi Downloader (Termux Tool) ===")
    print(Fore.YELLOW + "01. Normal Mode (Single file Downloading...)")
    print(Fore.YELLOW + "02. Parallel Mode (3 File Downloading...)\n")

    choice = input(Fore.GREEN + "Select an option (1 or 2): ").strip()

    if choice == "1":
        normal_mode()
    elif choice == "2":
        parallel_mode()
    else:
        print(Fore.RED + "[!] Invalid choice. Exiting...")

if __name__ == "__main__":
    main()
