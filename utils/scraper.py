# pln-news-monitor/utils/scraper.py

from newspaper import Article
from urllib.parse import urlparse

def scrape_news_data(url):
    """
    Scrape data berita lengkap menggunakan newspaper3k.
    Mengembalikan dictionary berisi data berita.
    """
    try:
        # Inisialisasi artikel dengan URL
        article = Article(url)

        # Unduh konten HTML
        article.download()
        # Parsing untuk mengekstrak informasi
        article.parse()

        # Ekstrak tanggal terbit jika tersedia
        publish_date = article.publish_date
        if publish_date:
            tanggal = str(publish_date.day)
            bulan = str(publish_date.month)
            tahun = str(publish_date.year)
        else:
            tanggal, bulan, tahun = None, None, None

        # Siapkan data dalam bentuk dictionary
        news_data = {
            "tanggal": tanggal,
            "bulan": bulan,
            "tahun": tahun,
            "media_pemberitaan": "Media Online", # Default value
            "judul_pemberitaan": article.title,
            "link_pemberitaan": url,
            "nama_media": article.source_url.replace('http://','').replace('https://','').replace('www.',''),
            "kategori_media": "Nasional" # Default value, bisa diubah dari form
        }
        return news_data

    except Exception as e:
        print(f"Gagal scrape {url}: {e}")
        return None