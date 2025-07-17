# pln-news-monitor/scheduler/monitor.py

import feedparser
from utils import database, scraper

# Daftar RSS Feed dari Google News untuk kata kunci "PLN"
SOURCES = {
    "PLN": "https://news.google.com/rss/search?q=PLN&hl=id&gl=ID&ceid=ID:id"
}

def run_monitoring():
    """Fungsi utama yang dijalankan oleh scheduler."""
    print(f"[{__name__}] Menjalankan pemantauan berita otomatis...")
    
    for keyword, url in SOURCES.items():
        feed = feedparser.parse(url)
        
        for entry in feed.entries:
            news_url = entry.link
            
            if not database.is_url_exist(news_url):
                print(f"[{__name__}] Berita baru ditemukan: {entry.title}")
                
                # DIUBAH: Panggil fungsi scraper yang benar
                news_data = scraper.scrape_news_data(news_url)
                
                if news_data:
                    # DIUBAH: Simpan data dictionary ke database
                    database.add_news(news_data)
                    print(f"[{__name__}] Berita '{news_data['judul_pemberitaan']}' berhasil disimpan.")
    
    print(f"[{__name__}] Pemantauan selesai.")