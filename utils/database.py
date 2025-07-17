# pln-news-monitor/utils/database.py

import sqlite3
from config import Config

DATABASE_NAME = Config.DATABASE_NAME

def get_db_connection():
    """Membuat koneksi ke database."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# Di dalam file utils/database.py

def init_db():
    """Membuat tabel berita dengan skema baru jika belum ada."""
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tanggal TEXT,
            bulan TEXT,
            tahun TEXT,
            media_pemberitaan TEXT,
            judul_pemberitaan TEXT NOT NULL,
            link_pemberitaan TEXT NOT NULL UNIQUE,
            nama_media TEXT,
            kategori_media TEXT
        );
    ''')
    conn.commit()
    conn.close()

# Anda juga perlu fungsi 'add_news' yang baru
def add_news(data):
    """Menambahkan berita baru dari dictionary."""
    conn = get_db_connection()
    try:
        conn.execute(
            '''INSERT INTO news (tanggal, bulan, tahun, media_pemberitaan, judul_pemberitaan, link_pemberitaan, nama_media, kategori_media) 
               VALUES (:tanggal, :bulan, :tahun, :media_pemberitaan, :judul_pemberitaan, :link_pemberitaan, :nama_media, :kategori_media)''',
            data
        )
        conn.commit()
    except sqlite3.IntegrityError:
        print(f"URL {data['link_pemberitaan']} sudah ada di database.")
    finally:
        conn.close()

def get_all_news():
    """Mengambil semua berita dari database, diurutkan dari yang terbaru."""
    conn = get_db_connection()
    news_list = conn.execute('SELECT * FROM news ORDER BY created_at DESC').fetchall()
    conn.close()
    return news_list

def get_news_by_id(news_id):
    """Mengambil satu berita berdasarkan ID."""
    conn = get_db_connection()
    news_item = conn.execute('SELECT * FROM news WHERE id = ?', (news_id,)).fetchone()
    conn.close()
    return news_item

def update_news(data):
    """Memperbarui data berita dari dictionary."""
    conn = get_db_connection()
    conn.execute(
        '''UPDATE news SET 
           judul_pemberitaan = :judul_pemberitaan, 
           media_pemberitaan = :media_pemberitaan, 
           kategori_media = :kategori_media 
           WHERE id = :id''',
        data
    )
    conn.commit()
    conn.close()

def delete_news_by_id(news_id):
    """Menghapus berita berdasarkan ID."""
    conn = get_db_connection()
    conn.execute('DELETE FROM news WHERE id = ?', (news_id,))
    conn.commit()
    conn.close()

# Di dalam file utils/database.py

def get_all_news():
    """Mengambil semua berita dari database, diurutkan dari yang terbaru."""
    conn = get_db_connection()
    # DIUBAH: Mengurutkan berdasarkan 'id' karena 'id' yang lebih besar berarti lebih baru
    news_list = conn.execute('SELECT * FROM news ORDER BY id DESC').fetchall()
    conn.close()
    return news_list

# Di dalam file utils/database.py

def is_url_exist(url):
    """Mengecek apakah URL sudah ada di database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    # DIUBAH: Menggunakan nama kolom yang benar 'link_pemberitaan'
    cursor.execute("SELECT id FROM news WHERE link_pemberitaan = ?", (url,))
    data = cursor.fetchone()
    conn.close()
    return data is not None

def delete_all_news():
    """Menghapus semua data dari tabel berita."""
    conn = get_db_connection()
    conn.execute('DELETE FROM news')
    conn.commit()
    conn.close()