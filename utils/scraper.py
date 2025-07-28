from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import WebDriverException
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from datetime import datetime
from dateutil.parser import parse as parse_date
import time

def scrape_news_data(url):
    """
    Scrape data berita lengkap menggunakan Selenium dan BeautifulSoup.
    """
    options = webdriver.ChromeOptions()
    options.add_argument('--headless') # Berjalan di background tanpa membuka jendela browser
    options.add_argument('--disable-gpu')
    options.add_argument('--log-level=3') # Mengurangi log yang tidak perlu
    options.add_experimental_option('excludeSwitches', ['enable-logging'])

    driver = None
    try:
        # Menginstal atau menggunakan driver yang sudah ada secara otomatis
        print("--- SCRAPER: Memulai WebDriver Manager ---")
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        print("--- SCRAPER: WebDriver berhasil dimulai. ---")
        
        driver.get(url)
        print(f"--- SCRAPER: Mengakses URL: {url} ---")
        time.sleep(3) # Beri waktu 3 detik agar semua elemen JavaScript termuat

        # Dapatkan judul halaman
        title = driver.title
        print(f"--- SCRAPER: Judul ditemukan: {title} ---")

        # Dapatkan tanggal (opsional, jika gagal akan menggunakan tanggal hari ini)
        publish_date_str = None
        dt = datetime.now() # Default ke waktu sekarang
        try:
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            # Coba cari tag 'time' dengan atribut 'datetime'
            time_tag = soup.find('time', {'datetime': True})
            # Coba cari meta property
            meta_tag = soup.find('meta', {'property': 'article:published_time'})
            
            if time_tag and time_tag.has_attr('datetime'):
                publish_date_str = time_tag['datetime']
            elif meta_tag and meta_tag.has_attr('content'):
                publish_date_str = meta_tag['content']
            
            if publish_date_str:
                dt = parse_date(publish_date_str)
                print(f"--- SCRAPER: Tanggal ditemukan: {dt.strftime('%Y-%m-%d')} ---")

        except Exception as date_e:
            print(f"--- SCRAPER: Peringatan, tanggal tidak ditemukan, menggunakan tanggal hari ini. Error: {date_e} ---")
            dt = datetime.now()

        news_data = {
            "tanggal": str(dt.day),
            "bulan": str(dt.month),
            "tahun": str(dt.year),
            "judul_pemberitaan": title.strip(),
            "link_pemberitaan": url,
            "nama_media": urlparse(url).netloc.replace('www.', ''),
            "media_pemberitaan": "Media Online", 
            "kategori_media": "Nasional" 
        }
        return news_data

    except WebDriverException as e:
        print(f"--- SCRAPER ERROR: Error WebDriver saat scraping {url}: {e} ---")
        return None
    except Exception as e:
        print(f"--- SCRAPER ERROR: Terjadi error tak terduga saat scraping {url}: {e} ---")
        return None
    finally:
        if driver:
            driver.quit()
        print("--- SCRAPER: Proses selesai, driver ditutup. ---")