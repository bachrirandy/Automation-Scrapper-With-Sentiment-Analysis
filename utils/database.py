import sqlite3
from config import Config

DATABASE_NAME = Config.DATABASE_NAME

def get_db_connection():
    """Membuat koneksi ke database."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Membuat tabel-tabel yang dibutuhkan."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Tabel untuk pemberitaan resmi (tanpa sentimen)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pemberitaan_resmi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tanggal TEXT, bulan TEXT, tahun TEXT,
            media_pemberitaan TEXT,
            judul_pemberitaan TEXT NOT NULL,
            link_pemberitaan TEXT NOT NULL UNIQUE,
            nama_media TEXT,
            kategori_media TEXT
        );
    ''')
    
    # Tabel untuk data analisis
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analisis_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tanggal TEXT, bulan TEXT, tahun TEXT,
            judul_pemberitaan TEXT NOT NULL,
            link_pemberitaan TEXT NOT NULL UNIQUE,
            nama_media TEXT,
            sentimen TEXT
        );
    ''')
    
    # Tabel untuk hasil pencarian berita sementara
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hasil_pencarian (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            judul_berita TEXT NOT NULL,
            link_pemberitaan TEXT NOT NULL UNIQUE,
            nama_media TEXT
        );
    ''')
    
    # Tabel keywords tidak lagi digunakan
    cursor.execute('DROP TABLE IF EXISTS keywords')
    
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
    # ▼▼▼ PERUBAHAN DI SINI ▼▼▼
    conn = get_db_connection()
    conn.execute(
        '''UPDATE pemberitaan_resmi SET 
           judul_pemberitaan = :judul_pemberitaan, 
           nama_media = :nama_media,
           tanggal = :tanggal,
           bulan = :bulan,
           tahun = :tahun,
           media_pemberitaan = :media_pemberitaan,
           kategori_media = :kategori_media 
           WHERE id = :id''',
        data
    )
    conn.commit()
    conn.close()
    # ▲▲▲ AKHIR PERUBAHAN ▲▲▲

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
    # (Kode fungsi ini tetap sama)
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
    # (Kode fungsi ini tetap sama)
    conn = get_db_connection()
    if sentiment and sentiment in ['Positif', 'Negatif', 'Netral']:
        query = "SELECT * FROM analisis_data WHERE sentimen = ? ORDER BY id DESC"
        analysis_list = conn.execute(query, (sentiment,)).fetchall()
    else:
        query = "SELECT * FROM analisis_data ORDER BY id DESC"
        analysis_list = conn.execute(query).fetchall()
    conn.close()
    return analysis_list

def get_all_positive_analisis_data():
    # (Kode fungsi ini tetap sama)
    conn = get_db_connection()
    query = "SELECT * FROM analisis_data WHERE sentimen = 'Positif' ORDER BY id DESC"
    positive_list = conn.execute(query).fetchall()
    conn.close()
    return positive_list

def get_latest_analisis_data(limit=10):
    # (Kode fungsi ini tetap sama)
    conn = get_db_connection()
    latest_analysis = conn.execute('SELECT * FROM analisis_data ORDER BY id DESC LIMIT ?', (limit,)).fetchall()
    conn.close()
    return latest_analysis

def get_analisis_data_by_id(analysis_id):
    # (Kode fungsi ini tetap sama)
    conn = get_db_connection()
    item = conn.execute('SELECT * FROM analisis_data WHERE id = ?', (analysis_id,)).fetchone()
    conn.close()
    return item

def update_analisis_data(data):
    # (Kode fungsi ini tetap sama)
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
    # (Kode fungsi ini tetap sama)
    conn = get_db_connection()
    conn.execute('DELETE FROM analisis_data WHERE id = ?', (analysis_id,))
    conn.commit()
    conn.close()

def delete_all_analisis_data():
    # (Kode fungsi ini tetap sama)
    conn = get_db_connection()
    conn.execute('DELETE FROM analisis_data')
    conn.commit()
    conn.close()
    
def is_analisis_url_exist(url):
    # (Kode fungsi ini tetap sama)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM analisis_data WHERE link_pemberitaan = ?", (url,))
    data = cursor.fetchone()
    conn.close()
    return data is not None

# --- BARU: Fungsi untuk Tabel 'hasil_pencarian' ---
def add_hasil_pencarian(data):
    """Menambahkan satu hasil pencarian ke tabel sementara."""
    conn = get_db_connection()
    try:
        conn.execute(
            'INSERT INTO hasil_pencarian (judul_berita, link_pemberitaan, nama_media) VALUES (?, ?, ?)',
            (data['judul_pemberitaan'], data['link_pemberitaan'], data['nama_media'])
        )
        conn.commit()
    except sqlite3.IntegrityError:
        pass # Abaikan jika link sudah ada
    except Exception as e:
        print(f"Error saat menambahkan hasil pencarian: {e}")
    finally:
        conn.close()

def get_all_hasil_pencarian():
    """Mengambil semua hasil pencarian dari tabel sementara."""
    conn = get_db_connection()
    hasil = conn.execute('SELECT * FROM hasil_pencarian ORDER BY id DESC').fetchall()
    conn.close()
    return hasil

def clear_hasil_pencarian():
    """Menghapus semua hasil pencarian dari tabel sementara."""
    conn = get_db_connection()
    conn.execute('DELETE FROM hasil_pencarian')
    conn.commit()
    conn.close()

def get_pencarian_by_link(link):
    """Mengambil satu item dari hasil pencarian berdasarkan link."""
    conn = get_db_connection()
    item = conn.execute('SELECT * FROM hasil_pencarian WHERE link_pemberitaan = ?', (link,)).fetchone()
    conn.close()
    return item
