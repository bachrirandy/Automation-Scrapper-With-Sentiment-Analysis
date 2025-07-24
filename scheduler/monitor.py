# pln-news-monitor/scheduler/monitor.py

import feedparser
from urllib.parse import quote
from utils import database, scraper, sentiment # Tambahkan import sentiment
import time

def run_monitoring():
    """
    Fungsi utama yang dijalankan scheduler.
    Mencari berita berdasarkan keyword, melakukan scraping, analisis sentimen,
    dan menyimpan hasil ke tabel analisis_data jika belum ada.
    """
    print(f"[{__name__}] Memulai pemantauan otomatis...")
    
    keywords_to_monitor = database.get_all_keywords()
    if not keywords_to_monitor:
        print(f"[{__name__}] Tidak ada keyword untuk dipantau. Proses dihentikan.")
        return

    print(f"[{__name__}] Memantau keywords: {[kw['keyword'] for kw in keywords_to_monitor]}")

    for kw_row in keywords_to_monitor:
        keyword = kw_row['keyword']
        # Gunakan quote untuk menangani spasi dan karakter khusus dalam keyword
        search_term = quote(keyword)
        source_url = f"https://news.google.com/rss/search?q={search_term}&hl=id&gl=ID&ceid=ID:id"
        
        try:
            feed = feedparser.parse(source_url)
            
            for entry in feed.entries:
                news_url = entry.link
                
                # PENTING: Cek duplikasi di kedua tabel agar tidak ada data ganda
                if not database.is_analisis_url_exist(news_url) and not database.is_pemberitaan_url_exist(news_url):
                    print(f"[{__name__}] Berita baru ditemukan untuk '{keyword}': {entry.title}")
                    
                    # Beri jeda sedikit antar request untuk tidak membebani server target
                    time.sleep(1) 
                    
                    news_data = scraper.scrape_news_data(news_url)
                    
                    if news_data:
                        # --- PERUBAHAN UTAMA ---
                        # Analisis sentimen menggunakan modul yang sudah dibuat
                        tonalitas = sentiment.analyze_title_sentiment(news_data['judul_pemberitaan'])
                        news_data['sentimen'] = tonalitas
                        
                        # Simpan ke tabel log analisis
                        database.add_analisis_data(news_data)
                        print(f"[{__name__}] Berita '{news_data['judul_pemberitaan']}' dengan sentimen '{tonalitas}' berhasil disimpan.")
        except Exception as e:
            print(f"[{__name__}] Gagal memproses keyword '{keyword}'. Error: {e}")

    print(f"[{__name__}] Pemantauan selesai.")