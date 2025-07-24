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

def get_filtered_analisis_data(sentiment=None):
    """Mengambil data analisis dengan filter sentimen."""
    conn = get_db_connection()
    if sentiment and sentiment in ['Positif', 'Negatif', 'Netral']:
        query = "SELECT * FROM analisis_data WHERE sentimen = ? ORDER BY id DESC"
        analysis_list = conn.execute(query, (sentiment,)).fetchall()
    else:
        query = "SELECT * FROM analisis_data ORDER BY id DESC"
        analysis_list = conn.execute(query).fetchall()
    conn.close()
    return analysis_list

# ▼▼▼ FUNGSI BARU DITAMBAHKAN ▼▼▼
def get_all_positive_analisis_data():
    """Mengambil semua data analisis dengan sentimen Positif."""
    conn = get_db_connection()
    query = "SELECT * FROM analisis_data WHERE sentimen = 'Positif' ORDER BY id DESC"
    positive_list = conn.execute(query).fetchall()
    conn.close()
    return positive_list
# ▲▲▲ AKHIR FUNGSI BARU ▲▲▲

def get_latest_analisis_data(limit=10):
    """Mengambil beberapa berita terbaru dari tabel analisis."""
    conn = get_db_connection()
    latest_analysis = conn.execute('SELECT * FROM analisis_data ORDER BY id DESC LIMIT ?', (limit,)).fetchall()
    conn.close()
    return latest_analysis

def get_analisis_data_by_id(analysis_id):
    """Mengambil satu data analisis berdasarkan ID."""
    conn = get_db_connection()
    item = conn.execute('SELECT * FROM analisis_data WHERE id = ?', (analysis_id,)).fetchone()
    conn.close()
    return item

def update_analisis_data(data):
    """Memperbarui data di tabel analisis_data."""
    conn = get_db_connection()
    conn.execute(
        '''UPDATE analisis_data SET 
           judul_pemberitaan = :judul_pemberitaan, 
           sentimen = :sentimen 
           WHERE id = :id''',
        data
    )
    conn.commit()
    conn.close()

def delete_analisis_data_by_id(analysis_id):
    """Menghapus satu data dari tabel analisis_data."""
    conn = get_db_connection()
    conn.execute('DELETE FROM analisis_data WHERE id = ?', (analysis_id,))
    conn.commit()
    conn.close()

def delete_all_analisis_data():
    """Menghapus semua data dari tabel analisis_data."""
    conn = get_db_connection()
    conn.execute('DELETE FROM analisis_data')
    conn.commit()
    conn.close()
    
def is_analisis_url_exist(url):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM analisis_data WHERE link_pemberitaan = ?", (url,))
    data = cursor.fetchone()
    conn.close()
    return data is not None

# --- Fungsi untuk Tabel 'keywords' ---
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