# pln-news-monitor/app.py

import atexit
import io
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from apscheduler.schedulers.background import BackgroundScheduler

from config import Config
from utils import database, scraper
from scheduler.monitor import run_monitoring

app = Flask(__name__)
app.config.from_object(Config)

# Inisialisasi database
with app.app_context():
    database.init_db()

# --- ROUTES ---

# ======================================================================
# RUTE BARU UNTUK HALAMAN SELAMAT DATANG
# ======================================================================
@app.route('/')
def home():
    """Rute untuk halaman selamat datang."""
    return render_template('home.html')

# ======================================================================
# RUTE LAMA 'dashboard' DIUBAH MENJADI 'pemberitaan'
# ======================================================================
@app.route('/pemberitaan')
def pemberitaan():
    """Rute untuk menampilkan tabel data berita."""
    news_list = database.get_all_news()
    # Pastikan Anda sudah me-rename file dashboard.html menjadi pemberitaan.html
    return render_template('pemberitaan.html', news_list=news_list)

@app.route('/add', methods=['POST'])
def add_news_route():
    url = request.form.get('url')
    media_pemberitaan = request.form.get('media_pemberitaan')
    kategori_media = request.form.get('kategori_media')

    if not url:
        flash('URL tidak boleh kosong!', 'danger')
        return redirect(url_for('pemberitaan')) # DIUBAH

    if database.is_url_exist(url):
        flash('Berita dengan URL tersebut sudah ada.', 'warning')
        return redirect(url_for('pemberitaan')) # DIUBAH

    news_data = scraper.scrape_news_data(url)

    if news_data:
        news_data['media_pemberitaan'] = media_pemberitaan
        news_data['kategori_media'] = kategori_media
        
        database.add_news(news_data)
        flash('Berita berhasil di-scrape dan ditambahkan!', 'success')
    else:
        flash('Gagal mengambil data dari URL. Pastikan link valid.', 'danger')
    
    return redirect(url_for('pemberitaan')) # DIUBAH

@app.route('/edit/<int:news_id>', methods=['GET', 'POST'])
def edit_news_route(news_id):
    news_item = database.get_news_by_id(news_id)
    if not news_item:
        return redirect(url_for('pemberitaan')) # DIUBAH

    if request.method == 'POST':
        data = {
            'id': news_id,
            'judul_pemberitaan': request.form.get('judul_pemberitaan'),
            'media_pemberitaan': request.form.get('media_pemberitaan'),
            'kategori_media': request.form.get('kategori_media')
        }
        database.update_news(data)
        flash('Berita berhasil diperbarui!', 'success')
        return redirect(url_for('pemberitaan')) # DIUBAH
        
    return render_template('edit.html', news=news_item)

@app.route('/delete/<int:news_id>', methods=['POST'])
def delete_news_route(news_id):
    database.delete_news_by_id(news_id)
    flash('Berita berhasil dihapus.', 'success')
    return redirect(url_for('pemberitaan')) # DIUBAH

@app.route('/reset', methods=['POST'])
def reset_all_data_route():
    database.delete_all_news()
    flash('Semua data berita telah berhasil direset.', 'warning')
    return redirect(url_for('pemberitaan')) # DIUBAH

@app.route('/download-excel')
def download_excel():
    conn = database.get_db_connection()
    df = pd.read_sql_query("SELECT * FROM news", conn)
    conn.close()
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Pemberitaan')
    output.seek(0)
    
    return send_file(
        output,
        as_attachment=True,
        download_name='laporan_pemberitaan.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

# --- SCHEDULER ---
scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(run_monitoring, 'interval', minutes=30)
scheduler.start()

atexit.register(lambda: scheduler.shutdown())

if __name__ == '__main__':
    app.run(debug=True)