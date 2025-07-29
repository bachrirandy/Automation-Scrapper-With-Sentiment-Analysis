# test_utama.py
from utils import scraper
import time

print("--- MEMULAI TES SCRAPER UTAMA ---")

# GANTI DENGAN LINK YANG GAGAL DI APLIKASI ANDA
url_yang_gagal = "https://aksesjambi.com/news/22/05/2025/pln-uid-s2jb-raih-penghargaan-tjsl-membina-umkm-kelompok-wanita-tani-beguyur/" 

print(f"Mencoba scrape URL: {url_yang_gagal}")
news_data = scraper.scrape_news_data(url_yang_gagal)

print("\n--- HASIL ---")
if news_data:
    print("✅ Scraping BERHASIL.")
    print(f"Data: {news_data}")
else:
    print("❌ Scraping GAGAL.")

print("--- TES SELESAI ---")