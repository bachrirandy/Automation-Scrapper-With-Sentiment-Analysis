# pln-news-monitor/utils/database.py

import sqlite3
from config import Config

DATABASE_NAME = Config.DATABASE_NAME

def get_db_connection():
    """Membuat koneksi ke database."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Membuat dua tabel terpisah: satu untuk pemberitaan resmi, satu untuk data analisis."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Tabel 1: Untuk data manual di halaman "Pemberitaan" (TANPA SENTIMEN)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pemberitaan_resmi (
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
    
    # Tabel 2: Untuk data otomatis dari monitoring (DENGAN SENTIMEN)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analisis_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tanggal TEXT,
            bulan TEXT,
            tahun TEXT,
            judul_pemberitaan TEXT NOT NULL,
            link_pemberitaan TEXT NOT NULL UNIQUE,
            nama_media TEXT,
            sentimen TEXT
        );
    ''')
    
    # Tabel untuk keywords tetap sama
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS keywords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT NOT NULL UNIQUE
        );
    ''')
    
    conn.commit()
    conn.close()

# --- Fungsi untuk Tabel 'pemberitaan_resmi' ---

def add_pemberitaan(data):
    """Menambahkan berita baru ke tabel pemberitaan resmi."""
    conn = get_db_connection()
    try:
        conn.execute(
            '''INSERT INTO pemberitaan_resmi (tanggal, bulan, tahun, media_pemberitaan, judul_pemberitaan, link_pemberitaan, nama_media, kategori_media) 
               VALUES (:tanggal, :bulan, :tahun, :media_pemberitaan, :judul_pemberitaan, :link_pemberitaan, :nama_media, :kategori_media)''',
            data
        )
        conn.commit()
    except Exception as e:
        print(f"Error saat menambahkan pemberitaan resmi: {e}")
    finally:
        conn.close()

def get_all_pemberitaan():
    """Mengambil semua berita dari tabel pemberitaan resmi."""
    conn = get_db_connection()
    news_list = conn.execute('SELECT * FROM pemberitaan_resmi ORDER BY id DESC').fetchall()
    conn.close()
    return news_list

def get_pemberitaan_by_id(news_id):
    conn = get_db_connection()
    news_item = conn.execute('SELECT * FROM pemberitaan_resmi WHERE id = ?', (news_id,)).fetchone()
    conn.close()
    return news_item

def update_pemberitaan(data):
    conn = get_db_connection()
    conn.execute(
        '''UPDATE pemberitaan_resmi SET 
           judul_pemberitaan = :judul_pemberitaan, 
           media_pemberitaan = :media_pemberitaan, 
           kategori_media = :kategori_media 
           WHERE id = :id''',
        data
    )
    conn.commit()
    conn.close()

def delete_pemberitaan_by_id(news_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM pemberitaan_resmi WHERE id = ?', (news_id,))
    conn.commit()
    conn.close()

def delete_all_pemberitaan():
    conn = get_db_connection()
    conn.execute('DELETE FROM pemberitaan_resmi')
    conn.commit()
    conn.close()

def is_pemberitaan_url_exist(url):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM pemberitaan_resmi WHERE link_pemberitaan = ?", (url,))
    data = cursor.fetchone()
    conn.close()
    return data is not None

# --- Fungsi untuk Tabel 'analisis_data' ---

def add_analisis_data(data):
    """Menambahkan berita baru ke tabel data analisis."""
    conn = get_db_connection()
    try:
        conn.execute(
            '''INSERT INTO analisis_data (tanggal, bulan, tahun, judul_pemberitaan, link_pemberitaan, nama_media, sentimen) 
               VALUES (:tanggal, :bulan, :tahun, :judul_pemberitaan, :link_pemberitaan, :nama_media, :sentimen)''',
            data
        )
        conn.commit()
    except Exception as e:
        print(f"Error saat menambahkan data analisis: {e}")
    finally:
        conn.close()
        
def is_analisis_url_exist(url):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM analisis_data WHERE link_pemberitaan = ?", (url,))
    data = cursor.fetchone()
    conn.close()
    return data is not None

# --- Fungsi untuk Tabel 'keywords' (tetap sama) ---
def add_keyword(keyword):
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO keywords (keyword) VALUES (?)', (keyword,))
        conn.commit()
    except sqlite3.IntegrityError:
        print(f"Keyword '{keyword}' sudah ada.")
    finally:
        conn.close()

def get_all_keywords():
    conn = get_db_connection()
    keywords = conn.execute('SELECT * FROM keywords ORDER BY keyword ASC').fetchall()
    conn.close()
    return keywords

def delete_keyword(keyword_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM keywords WHERE id = ?', (keyword_id,))
    conn.commit()
    conn.close()
