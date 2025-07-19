# pln-news-monitor/scheduler/monitor.py

import feedparser
from urllib.parse import quote
from utils import database, scraper
import random

def run_monitoring():
    """
    Fungsi utama yang dijalankan scheduler.
    Menyimpan hasil ke tabel analisis_data.
    """
    print(f"[{__name__}] Memulai pemantauan otomatis...")
    
    keywords_to_monitor = database.get_all_keywords()
    if not keywords_to_monitor:
        print(f"[{__name__}] Tidak ada keyword untuk dipantau. Proses dihentikan.")
        return

    print(f"[{__name__}] Memantau keywords: {[kw['keyword'] for kw in keywords_to_monitor]}")

    for kw_row in keywords_to_monitor:
        keyword = kw_row['keyword']
        search_term = quote(keyword)
        source_url = f"https://news.google.com/rss/search?q={search_term}&hl=id&gl=ID&ceid=ID:id"
        
        feed = feedparser.parse(source_url)
        
        for entry in feed.entries:
            news_url = entry.link
            
            # Cek duplikat di tabel analisis
            if not database.is_analisis_url_exist(news_url):
                print(f"[{__name__}] Berita baru ditemukan untuk '{keyword}': {entry.title}")
                
                news_data = scraper.scrape_news_data(news_url)
                
                if news_data:
                    # Tambahkan sentimen dummy
                    sentimen_dummy = ['Positif', 'Negatif', 'Netral']
                    news_data['sentimen'] = random.choice(sentimen_dummy)
                    
                    # Simpan ke tabel analisis_data
                    database.add_analisis_data(news_data)
                    print(f"[{__name__}] Berita '{news_data['judul_pemberitaan']}' berhasil disimpan ke log analisis.")
    
    print(f"[{__name__}] Pemantauan selesai.")
