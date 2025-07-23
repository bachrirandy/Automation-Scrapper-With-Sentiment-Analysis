# pln-news-monitor/app.py

import atexit
import io
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.base import JobLookupError
import random
from datetime import datetime, timedelta

from config import Config
from utils import database, scraper
from scheduler.monitor import run_monitoring

app = Flask(__name__)
app.config.from_object(Config)

# --- SCHEDULER SETUP ---
scheduler = BackgroundScheduler(daemon=True)
# Menambahkan job dengan ID agar bisa dikontrol
scheduler.add_job(run_monitoring, 'interval', minutes=30, id='monitoring_job')
scheduler.start()
# Matikan scheduler dengan benar saat aplikasi keluar
atexit.register(lambda: scheduler.shutdown())


# Inisialisasi database
with app.app_context():
    database.init_db()

# --- ROUTES ---

@app.route('/')
def home():
    """Rute untuk halaman selamat datang."""
    return render_template('dashboard/home.html')

@app.route('/analisis')
def analisis():
    """Rute untuk dasbor statistik sentimen (menggunakan tabel analisis_data)."""
    sentiment_filter = request.args.get('filter', None)
    
    conn = database.get_db_connection()
    full_df = pd.read_sql_query("SELECT * FROM analisis_data", conn)
    conn.close()

    # Hitung statistik kartu dari keseluruhan data (selalu tampilkan total)
    total_berita = len(full_df)
    positif_count, negatif_count, netral_count = 0, 0, 0
    if not full_df.empty and 'sentimen' in full_df.columns:
        sentimen_counts_total = full_df['sentimen'].value_counts()
        positif_count = int(sentimen_counts_total.get('Positif', 0))
        negatif_count = int(sentimen_counts_total.get('Negatif', 0))
        netral_count = int(sentimen_counts_total.get('Netral', 0))

    # Siapkan DataFrame untuk chart berdasarkan filter
    if sentiment_filter and not full_df.empty:
        df_for_charts = full_df[full_df['sentimen'] == sentiment_filter]
    else:
        df_for_charts = full_df

    # Hitung data untuk SEMUA chart menggunakan DataFrame yang sudah difilter
    sentimen_labels, sentimen_data, sentimen_colors = [], [], []
    color_map = {'Positif': '#198754', 'Negatif': '#dc3545', 'Netral': '#6c757d'}
    if not df_for_charts.empty and 'sentimen' in df_for_charts.columns:
        sentimen_counts_chart = df_for_charts['sentimen'].value_counts()
        sentimen_labels = sentimen_counts_chart.index.tolist()
        sentimen_data = sentimen_counts_chart.values.tolist()
        sentimen_colors = [color_map.get(label, '#CCCCCC') for label in sentimen_labels]

    analysis_list = database.get_filtered_analisis_data(sentiment_filter)
    
    # DIUBAH: Inisialisasi variabel tren sebagai list kosong di awal
    trend_labels, trend_positif, trend_negatif, trend_netral = [], [], [], []
    if not df_for_charts.empty:
        # Konversi kolom tanggal/bulan/tahun menjadi satu kolom datetime
        df_for_charts['tanggal_lengkap'] = pd.to_datetime(df_for_charts['tahun'].astype(str) + '-' + df_for_charts['bulan'].astype(str) + '-' + df_for_charts['tanggal'].astype(str), errors='coerce')
        df_for_charts.dropna(subset=['tanggal_lengkap'], inplace=True)
        
        seven_days_ago = datetime.now() - timedelta(days=7)
        df_last_7_days = df_for_charts[df_for_charts['tanggal_lengkap'] >= seven_days_ago]
        
        if not df_last_7_days.empty:
            sentiment_trend = df_last_7_days.groupby([df_last_7_days['tanggal_lengkap'].dt.date, 'sentimen']).size().unstack(fill_value=0).reindex(columns=['Positif', 'Negatif', 'Netral'], fill_value=0)
            trend_labels = [d.strftime('%b %d') for d in sentiment_trend.index]
            trend_positif = sentiment_trend['Positif'].tolist()
            trend_negatif = sentiment_trend['Negatif'].tolist()
            trend_netral = sentiment_trend['Netral'].tolist()

    top_positif_media, top_negatif_media = pd.Series(dtype='int64'), pd.Series(dtype='int64')
    if not df_for_charts.empty and 'sentimen' in df_for_charts.columns:
        top_positif_media = df_for_charts[df_for_charts['sentimen'] == 'Positif']['nama_media'].value_counts().head(5)
        top_negatif_media = df_for_charts[df_for_charts['sentimen'] == 'Negatif']['nama_media'].value_counts().head(5)

    return render_template(
        'analisis/analisis.html',
        total_berita=total_berita, positif_count=positif_count, negatif_count=negatif_count, netral_count=netral_count,
        sentimen_labels=sentimen_labels, sentimen_data=sentimen_data, sentimen_colors=sentimen_colors,
        analysis_list=analysis_list, active_filter=sentiment_filter,
        trend_labels=trend_labels, 
        trend_positif_data=trend_positif, 
        trend_negatif_data=trend_negatif, 
        trend_netral_data=trend_netral,
        top_positif_media=top_positif_media.to_dict(), 
        top_negatif_media=top_negatif_media.to_dict()
    )

# --- Rute CRUD untuk Halaman Analisis ---
@app.route('/analisis/edit/<int:analysis_id>', methods=['GET', 'POST'])
def edit_analisis_route(analysis_id):
    item = database.get_analisis_data_by_id(analysis_id)
    if not item:
        return redirect(url_for('analisis'))
    if request.method == 'POST':
        data = {'id': analysis_id, 'judul_pemberitaan': request.form.get('judul_pemberitaan'), 'sentimen': request.form.get('sentimen')}
        database.update_analisis_data(data)
        flash('Data analisis berhasil diperbarui!', 'success')
        return redirect(url_for('analisis'))
    return render_template('analisis/edit_analisis.html', item=item)

@app.route('/analisis/delete/<int:analysis_id>', methods=['POST'])
def delete_analisis_route(analysis_id):
    database.delete_analisis_data_by_id(analysis_id)
    flash('Data analisis berhasil dihapus.', 'success')
    return redirect(url_for('analisis'))

@app.route('/analisis/reset', methods=['POST'])
def reset_analisis_route():
    database.delete_all_analisis_data()
    flash('Semua data log analisis telah direset.', 'warning')
    return redirect(url_for('analisis'))

@app.route('/analisis/promote/<int:analysis_id>', methods=['POST'])
def promote_news_route(analysis_id):
    """Memindahkan berita dari log analisis ke tabel pemberitaan resmi."""
    item_to_promote = database.get_analisis_data_by_id(analysis_id)
    if not item_to_promote:
        flash("Berita tidak ditemukan.", "danger")
        return redirect(url_for('analisis'))

    url = item_to_promote['link_pemberitaan']
    if database.is_pemberitaan_url_exist(url):
        flash(f"Berita dari '{item_to_promote['nama_media']}' sudah ada di tabel pemberitaan.", "warning")
        return redirect(url_for('analisis'))

    news_data = dict(item_to_promote)
    news_data['media_pemberitaan'] = "Media Online"
    news_data['kategori_media'] = "Dipromosikan dari Analisis"

    database.add_pemberitaan(news_data)
    flash(f"Berita '{item_to_promote['judul_pemberitaan']}' berhasil dipromosikan ke tabel pemberitaan.", "success")
    return redirect(url_for('analisis'))

# --- Rute CRUD untuk Halaman Pemberitaan ---
@app.route('/pemberitaan')
def pemberitaan():
    news_list = database.get_all_pemberitaan()
    return render_template('berita/pemberitaan.html', news_list=news_list)

@app.route('/add', methods=['POST'])
def add_news_route():
    url = request.form.get('url')
    media_pemberitaan = request.form.get('media_pemberitaan')
    kategori_media = request.form.get('kategori_media')
    if not url:
        flash('URL tidak boleh kosong!', 'danger')
        return redirect(url_for('pemberitaan'))
    if database.is_pemberitaan_url_exist(url):
        flash('Berita dengan URL tersebut sudah ada.', 'warning')
        return redirect(url_for('pemberitaan'))
    news_data = scraper.scrape_news_data(url)
    if news_data:
        news_data['media_pemberitaan'] = media_pemberitaan
        news_data['kategori_media'] = kategori_media
        sentimen_dummy = ['Positif', 'Negatif', 'Netral']
        news_data['sentimen'] = random.choice(sentimen_dummy)
        database.add_pemberitaan(news_data)
        database.add_analisis_data(news_data)
        flash(f"Berita berhasil ditambahkan!", 'success')
    else:
        flash('Gagal mengambil data dari URL. Pastikan link valid.', 'danger')
    return redirect(url_for('pemberitaan'))

@app.route('/edit/<int:news_id>', methods=['GET', 'POST'])
def edit_news_route(news_id):
    news_item = database.get_pemberitaan_by_id(news_id)
    if not news_item:
        return redirect(url_for('pemberitaan'))
    if request.method == 'POST':
        data = {'id': news_id, 'judul_pemberitaan': request.form.get('judul_pemberitaan'), 'media_pemberitaan': request.form.get('media_pemberitaan'), 'kategori_media': request.form.get('kategori_media')}
        database.update_pemberitaan(data)
        flash('Berita berhasil diperbarui!', 'success')
        return redirect(url_for('pemberitaan'))
    return render_template('berita/edit.html', news=news_item)

@app.route('/delete/<int:news_id>', methods=['POST'])
def delete_news_route(news_id):
    database.delete_pemberitaan_by_id(news_id)
    flash('Berita berhasil dihapus.', 'success')
    return redirect(url_for('pemberitaan'))

@app.route('/reset', methods=['POST'])
def reset_all_data_route():
    database.delete_all_pemberitaan()
    flash('Semua data berita telah berhasil direset.', 'warning')
    return redirect(url_for('pemberitaan'))

@app.route('/download-excel')
def download_excel():
    """Mengunduh data dari tabel pemberitaan_resmi."""
    conn = database.get_db_connection()
    df = pd.read_sql_query("SELECT * FROM pemberitaan_resmi", conn)
    conn.close()
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Pemberitaan')
    output.seek(0)
    return send_file(output, as_attachment=True, download_name='laporan_pemberitaan.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

# --- Rute Monitoring ---
@app.route('/monitoring')
def monitoring_route():
    keywords = database.get_all_keywords()
    latest_analysis = database.get_latest_analisis_data(limit=10)
    job = scheduler.get_job('monitoring_job')
    is_running = job is not None and job.next_run_time is not None
    return render_template('dashboard/monitoring.html', keywords=keywords, latest_analysis=latest_analysis, is_running=is_running)

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

@app.route('/monitoring/toggle', methods=['POST'])
def toggle_scheduler_route():
    """Menghentikan atau menjalankan kembali scheduler."""
    job = scheduler.get_job('monitoring_job')
    if job is not None and job.next_run_time is not None:
        scheduler.pause_job('monitoring_job')
        flash("Scheduler pemantauan otomatis telah dihentikan.", "warning")
    else:
        scheduler.resume_job('monitoring_job')
        flash("Scheduler pemantauan otomatis telah dijalankan kembali.", "success")
    return redirect(url_for('monitoring_route'))

if __name__ == '__main__':
    app.run(debug=True)
