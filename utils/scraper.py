# pln-news-monitor/utils/scraper.py

from requests_html import HTMLSession
from urllib.parse import urlparse
from datetime import datetime
from dateutil.parser import parse as parse_date
import re

def scrape_news_data(url):
    """
    Scrape data berita lengkap menggunakan requests-html yang mampu merender JavaScript.
    """
    try:
        # --- Tahap 1: Inisialisasi Sesi dan Render Halaman ---
        session = HTMLSession()
        response = session.get(url, timeout=20)
        
        # Jalankan JavaScript di halaman (ini adalah langkah kunci)
        # sleep=1 memberi waktu 1 detik untuk elemen-elemen muncul
        response.html.render(sleep=1, timeout=30)
        
        # --- Tahap 2: Ekstraksi Judul dengan Berbagai Metode ---
        title = None
        title_selectors = [
            'meta[property="og:title"]',  # Prioritas 1: Open Graph Title
            'h1',                        # Prioritas 2: Judul Utama Halaman
            'title'                      # Prioritas 3: Judul Tab Browser
        ]
        
        for selector in title_selectors:
            element = response.html.find(selector, first=True)
            if element:
                # Jika tag meta, ambil dari atribut 'content'
                if 'property' in element.attrs and element.attrs['property'] == 'og:title':
                    title = element.attrs.get('content')
                # Jika tag lain, ambil teksnya
                else:
                    title = element.text
                
                if title:
                    break # Hentikan pencarian jika judul sudah ditemukan
        
        if not title:
            title = "Judul tidak dapat diekstrak"

        # --- Tahap 3: Ekstraksi Tanggal dengan Berbagai Metode ---
        publish_date_str = None
        date_selectors = [
            'meta[property="article:published_time"]', # Prioritas 1
            'time[datetime]',                         # Prioritas 2
            '.published-date',                        # Kelas umum
            '.post-date',                             # Kelas umum lainnya
            '#publish_date'                           # ID umum
        ]

        for selector in date_selectors:
            element = response.html.find(selector, first=True)
            if element:
                if 'content' in element.attrs:
                    publish_date_str = element.attrs['content']
                elif 'datetime' in element.attrs:
                    publish_date_str = element.attrs['datetime']
                else:
                    publish_date_str = element.text
                
                if publish_date_str:
                    break
        
        # Fallback menggunakan Regex jika selector gagal
        if not publish_date_str:
            date_pattern = re.compile(r'\d{1,2}\s+\w+\s+\d{4}')
            match = date_pattern.search(response.html.text)
            if match:
                publish_date_str = match.group(0)

        # --- Tahap 4: Parsing Tanggal ---
        try:
            # Gunakan dateutil untuk mem-parsing berbagai format tanggal
            dt = parse_date(publish_date_str)
            tanggal, bulan, tahun = str(dt.day), str(dt.month), str(dt.year)
        except (ValueError, TypeError):
            # Jika parsing gagal atau tanggal tidak ditemukan, gunakan tanggal hari ini
            print(f"Peringatan: Tanggal tidak ditemukan/dikenali untuk {url}. Menggunakan tanggal hari ini.")
            now = datetime.now()
            tanggal, bulan, tahun = str(now.day), str(now.month), str(now.year)

        # Siapkan data dalam bentuk dictionary
        news_data = {
            "tanggal": tanggal,
            "bulan": bulan,
            "tahun": tahun,
            "judul_pemberitaan": title.strip(),
            "link_pemberitaan": url,
            "nama_media": urlparse(url).netloc.replace('www.', ''),
            "media_pemberitaan": "Media Online", 
            "kategori_media": "Nasional" 
        }
        return news_data

    except Exception as e:
        print(f"Terjadi error tak terduga saat scraping {url}: {e}")
        return None
