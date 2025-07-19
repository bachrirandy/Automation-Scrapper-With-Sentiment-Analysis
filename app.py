# pln-news-monitor/app.py

import atexit
import io
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from apscheduler.schedulers.background import BackgroundScheduler
import random
from datetime import datetime, timedelta

from config import Config
from utils import database, scraper
from scheduler.monitor import run_monitoring

app = Flask(__name__)
app.config.from_object(Config)

# Inisialisasi database
with app.app_context():
    database.init_db()

# --- ROUTES ---

@app.route('/')
def home():
    """Rute untuk halaman selamat datang."""
    return render_template('home.html')

@app.route('/analisis')
def analisis():
    """Rute untuk dasbor statistik sentimen (menggunakan tabel analisis_data)."""
    conn = database.get_db_connection()
    # Mengambil data dari tabel analisis
    df = pd.read_sql_query("SELECT * FROM analisis_data", conn)
    conn.close()

    total_berita = len(df)
    # ... (sisa logika statistik tetap sama)
    positif_count, negatif_count, netral_count = 0, 0, 0
    sentimen_labels, sentimen_data = [], []
    if not df.empty and 'sentimen' in df.columns:
        sentimen_counts = df['sentimen'].value_counts()
        sentimen_labels = sentimen_counts.index.tolist()
        sentimen_data = sentimen_counts.values.tolist()
        positif_count = int(sentimen_counts.get('Positif', 0))
        negatif_count = int(sentimen_counts.get('Negatif', 0))
        netral_count = int(sentimen_counts.get('Netral', 0))
    latest_news = [] # Untuk analisis, kita mungkin tidak perlu berita terbaru di sini
    trend_labels, trend_positif, trend_negatif, trend_netral = [], [], [], []
    if not df.empty:
        df['tanggal_lengkap'] = pd.to_datetime(df['tahun'].astype(str) + '-' + df['bulan'].astype(str) + '-' + df['tanggal'].astype(str), errors='coerce')
        df.dropna(subset=['tanggal_lengkap'], inplace=True)
        seven_days_ago = datetime.now() - timedelta(days=7)
        df_last_7_days = df[df['tanggal_lengkap'] >= seven_days_ago]
        if not df_last_7_days.empty:
            sentiment_trend = df_last_7_days.groupby([df_last_7_days['tanggal_lengkap'].dt.date, 'sentimen']).size().unstack(fill_value=0).reindex(columns=['Positif', 'Negatif', 'Netral'], fill_value=0)
            trend_labels = [d.strftime('%b %d') for d in sentiment_trend.index]
            trend_positif = sentiment_trend['Positif'].tolist()
            trend_negatif = sentiment_trend['Negatif'].tolist()
            trend_netral = sentiment_trend['Netral'].tolist()
    top_positif_media, top_negatif_media = pd.Series(dtype='int64'), pd.Series(dtype='int64')
    if not df.empty and 'sentimen' in df.columns:
        top_positif_media = df[df['sentimen'] == 'Positif']['nama_media'].value_counts().head(5)
        top_negatif_media = df[df['sentimen'] == 'Negatif']['nama_media'].value_counts().head(5)

    return render_template(
        'analisis.html',
        total_berita=total_berita, positif_count=positif_count, negatif_count=negatif_count, netral_count=netral_count,
        sentimen_labels=sentimen_labels, sentimen_data=sentimen_data, latest_news=latest_news,
        trend_labels=trend_labels, trend_positif_data=trend_positif, trend_negatif_data=trend_negatif, trend_netral_data=trend_netral,
        top_positif_media=top_positif_media.to_dict(), top_negatif_media=top_negatif_media.to_dict()
    )

@app.route('/pemberitaan')
def pemberitaan():
    """Rute untuk menampilkan tabel data berita resmi."""
    news_list = database.get_all_pemberitaan() # Menggunakan fungsi baru
    return render_template('pemberitaan.html', news_list=news_list)

@app.route('/add', methods=['POST'])
def add_news_route():
    """Menyimpan berita ke tabel pemberitaan_resmi (tanpa sentimen)."""
    url = request.form.get('url')
    media_pemberitaan = request.form.get('media_pemberitaan')
    kategori_media = request.form.get('kategori_media')
    if not url:
        flash('URL tidak boleh kosong!', 'danger')
        return redirect(url_for('pemberitaan'))
    if database.is_pemberitaan_url_exist(url): # Menggunakan fungsi cek baru
        flash('Berita dengan URL tersebut sudah ada.', 'warning')
        return redirect(url_for('pemberitaan'))
    news_data = scraper.scrape_news_data(url)
    if news_data:
        news_data['media_pemberitaan'] = media_pemberitaan
        news_data['kategori_media'] = kategori_media
        # Tidak ada penambahan sentimen di sini
        database.add_pemberitaan(news_data) # Menggunakan fungsi add baru
        flash(f"Berita berhasil ditambahkan!", 'success')
    else:
        flash('Gagal mengambil data dari URL. Pastikan link valid.', 'danger')
    return redirect(url_for('pemberitaan'))

@app.route('/edit/<int:news_id>', methods=['GET', 'POST'])
def edit_news_route(news_id):
    news_item = database.get_pemberitaan_by_id(news_id) # Menggunakan fungsi get baru
    if not news_item:
        return redirect(url_for('pemberitaan'))
    if request.method == 'POST':
        data = {'id': news_id, 'judul_pemberitaan': request.form.get('judul_pemberitaan'), 'media_pemberitaan': request.form.get('media_pemberitaan'), 'kategori_media': request.form.get('kategori_media')}
        database.update_pemberitaan(data) # Menggunakan fungsi update baru
        flash('Berita berhasil diperbarui!', 'success')
        return redirect(url_for('pemberitaan'))
    return render_template('edit.html', news=news_item)

@app.route('/delete/<int:news_id>', methods=['POST'])
def delete_news_route(news_id):
    database.delete_pemberitaan_by_id(news_id) # Menggunakan fungsi delete baru
    flash('Berita berhasil dihapus.', 'success')
    return redirect(url_for('pemberitaan'))

@app.route('/reset', methods=['POST'])
def reset_all_data_route():
    database.delete_all_pemberitaan() # Menggunakan fungsi reset baru
    flash('Semua data berita telah berhasil direset.', 'warning')
    return redirect(url_for('pemberitaan'))

@app.route('/download-excel')
def download_excel():
    """Mengunduh data dari tabel pemberitaan_resmi."""
    conn = database.get_db_connection()
    df = pd.read_sql_query("SELECT * FROM pemberitaan_resmi", conn) # Mengambil dari tabel resmi
    conn.close()
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Pemberitaan')
    output.seek(0)
    return send_file(output, as_attachment=True, download_name='laporan_pemberitaan.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

# ... (sisa rute monitoring tetap sama)
@app.route('/monitoring')
def monitoring_route():
    keywords = database.get_all_keywords()
    return render_template('monitoring.html', keywords=keywords)

@app.route('/monitoring/add', methods=['POST'])
def add_keyword_route():
    keyword = request.form.get('keyword')
    if keyword:
        database.add_keyword(keyword.strip())
        flash(f"Keyword '{keyword}' berhasil ditambahkan untuk pemantauan.", "success")
    else:
        flash("Keyword tidak boleh kosong.", "danger")
    return redirect(url_for('monitoring_route'))

@app.route('/monitoring/delete/<int:keyword_id>', methods=['POST'])
def delete_keyword_route(keyword_id):
    database.delete_keyword(keyword_id)
    flash("Keyword berhasil dihapus.", "success")
    return redirect(url_for('monitoring_route'))

@app.route('/monitoring/run', methods=['POST'])
def run_monitoring_now():
    try:
        run_monitoring()
        flash("Pemantauan manual berhasil dijalankan. Cek halaman 'Dashboard Analisis' untuk hasilnya.", "success")
    except Exception as e:
        flash(f"Terjadi error saat menjalankan pemantauan: {e}", "danger")
    return redirect(url_for('monitoring_route'))

# --- SCHEDULER ---
scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(run_monitoring, 'interval', minutes=30)
scheduler.start()

atexit.register(lambda: scheduler.shutdown())

if __name__ == '__main__':
    app.run(debug=True)
