import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from urllib.parse import urlparse
from datetime import datetime
from dateutil.parser import parse as parse_date
import os

def parse_html_and_get_data(html_content, url):
    """Fungsi bantuan untuk mem-parsing judul dan tanggal dari konten HTML."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    title = None
    if soup.find('meta', property='og:title'):
        title = soup.find('meta', property='og:title').get('content')
    elif soup.find('h1'):
        title = soup.find('h1').get_text()
    elif soup.find('title'):
        title = soup.find('title').get_text()

    dt = datetime.now()
    try:
        time_tag = soup.find('time', {'datetime': True})
        meta_tag = soup.find('meta', {'property': 'article:published_time'})
        if time_tag and time_tag.has_attr('datetime'):
            dt = parse_date(time_tag['datetime'])
        elif meta_tag and meta_tag.has_attr('content'):
            dt = parse_date(meta_tag['content'])
    except Exception:
        pass
        
    if title and title.strip():
        return {
            "tanggal": str(dt.day), "bulan": str(dt.month), "tahun": str(dt.year),
            "judul_pemberitaan": title.strip(), "link_pemberitaan": url,
            "nama_media": urlparse(url).netloc.replace('www.', ''),
            "media_pemberitaan": "Media Online", "kategori_media": "Nasional" 
        }
    return None

def fetch_with_selenium(url):
    """Metode andal menggunakan Selenium sebagai fallback."""
    print("--- SCRAPER: Menjalankan metode fallback dengan Selenium. ---")
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--log-level=3')
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.add_argument("--blink-settings=imagesEnabled=false")

    driver = None
    try:
        driver_path = os.path.join(os.getcwd(), 'chromedriver.exe')
        if not os.path.exists(driver_path):
            print(f"--- SCRAPER ERROR: chromedriver.exe tidak ditemukan di path: {driver_path} ---")
            return None
            
        service = ChromeService(executable_path=driver_path)
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(url)
        WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.TAG_NAME, "title")))
        
        return parse_html_and_get_data(driver.page_source, url)

    except TimeoutException:
        print(f"--- SCRAPER ERROR (Selenium): Waktu tunggu habis saat memuat {url} ---")
        return None
    except Exception as e:
        print(f"--- SCRAPER ERROR (Selenium): Terjadi error tak terduga: {e} ---")
        return None
    finally:
        if driver:
            driver.quit()

def scrape_news_data(url):
    """
    Scrape satu URL menggunakan metode hibrida.
    """
    # Cek dulu apakah inputnya URL atau bukan
    if not url or not url.strip().startswith(('http://', 'https://')):
        # Jika teks biasa, buat data manual
        return {
            "tanggal": datetime.now().day,
            "bulan": datetime.now().month,
            "tahun": datetime.now().year,
            "judul_pemberitaan": url,
            "link_pemberitaan": f"manual_input_{datetime.now().timestamp()}",
            "nama_media": "Input Manual",
        }

    # --- Percobaan 1: Metode Cepat ---
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=8, allow_redirects=True)
        response.raise_for_status()
        
        # Gunakan response.url untuk mendapatkan URL final setelah redirect
        news_data = parse_html_and_get_data(response.text, response.url)

        if news_data:
            print(f"--- SCRAPER: Metode cepat berhasil untuk {url} ---")
            return news_data
        else:
             # Jika judul tidak ditemukan, paksa untuk menggunakan Selenium
            raise ValueError("Judul tidak ditemukan, mungkin butuh JavaScript.")

    except (requests.exceptions.RequestException, ValueError) as e:
        print(f"--- SCRAPER: Metode cepat gagal ({e}), beralih ke Selenium. ---")
        return fetch_with_selenium(url)
