import atexit
import io
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta

from config import Config
from utils import database, scraper, sentiment
from scheduler.monitor import run_monitoring

app = Flask(__name__)
app.config.from_object(Config)

# --- SCHEDULER SETUP ---
scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(run_monitoring, 'interval', minutes=60, id='monitoring_job')
scheduler.start()
atexit.register(lambda: scheduler.shutdown())

# Inisialisasi database
with app.app_context():
    database.init_db()

# --- ROUTES ---

@app.route('/')
def home():
    return render_template('dashboard/home.html')

@app.route('/analisis')
def analisis():
    sentiment_filter = request.args.get('filter', None)
    
    conn = database.get_db_connection()
    try:
        full_df = pd.read_sql_query("SELECT * FROM analisis_data", conn)
    except pd.io.sql.DatabaseError:
        full_df = pd.DataFrame()
    conn.close()

    total_berita = len(full_df)
    positif_count, negatif_count, netral_count = 0, 0, 0
    if not full_df.empty and 'sentimen' in full_df.columns:
        sentimen_counts_total = full_df['sentimen'].value_counts()
        positif_count = int(sentimen_counts_total.get('Positif', 0))
        negatif_count = int(sentimen_counts_total.get('Negatif', 0))
        netral_count = int(sentimen_counts_total.get('Netral', 0))

    if sentiment_filter and not full_df.empty:
        df_for_charts = full_df[full_df['sentimen'] == sentiment_filter].copy()
    else:
        df_for_charts = full_df.copy()

    sentimen_labels, sentimen_data, sentimen_colors = [], [], []
    color_map = {'Positif': '#198754', 'Negatif': '#dc3545', 'Netral': '#6c757d'}
    if not df_for_charts.empty and 'sentimen' in df_for_charts.columns:
        sentimen_counts_chart = df_for_charts['sentimen'].value_counts()
        sentimen_labels = sentimen_counts_chart.index.tolist()
        sentimen_data = sentimen_counts_chart.values.tolist()
        sentimen_colors = [color_map.get(label, '#CCCCCC') for label in sentimen_labels]

    analysis_list = database.get_filtered_analisis_data(sentiment_filter)
    
    trend_labels, trend_positif, trend_negatif, trend_netral = [], [], [], []
    if not df_for_charts.empty:
        df_for_charts['tanggal_lengkap'] = pd.to_datetime(df_for_charts['tahun'].astype(str) + '-' + df_for_charts['bulan'].astype(str) + '-' + df_for_charts['tanggal'].astype(str), errors='coerce')
        df_for_charts.dropna(subset=['tanggal_lengkap'], inplace=True)
        
        if not df_for_charts.empty:
            seven_days_ago = datetime.now() - timedelta(days=7)
            df_last_7_days = df_for_charts[df_for_charts['tanggal_lengkap'] >= seven_days_ago]
            
            if not df_last_7_days.empty:
                sentiment_trend = df_last_7_days.groupby([df_last_7_days['tanggal_lengkap'].dt.date, 'sentimen']).size().unstack(fill_value=0).reindex(columns=['Positif', 'Negatif', 'Netral'], fill_value=0)
                if not sentiment_trend.empty:
                    trend_labels = [d.strftime('%b %d') for d in sentiment_trend.index]
                    trend_positif = sentiment_trend['Positif'].tolist()
                    trend_negatif = sentiment_trend['Negatif'].tolist()
                    trend_netral = sentiment_trend['Netral'].tolist()

    return render_template(
        'analisis/analisis.html',
        total_berita=total_berita, positif_count=positif_count, negatif_count=negatif_count, netral_count=netral_count,
        sentimen_labels=sentimen_labels, sentimen_data=sentimen_data, sentimen_colors=sentimen_colors,
        analysis_list=analysis_list, active_filter=sentiment_filter,
        trend_labels=trend_labels, trend_positif_data=trend_positif, trend_negatif_data=trend_negatif, trend_netral_data=trend_netral,
        latest_news=database.get_latest_analisis_data(5)
    )

@app.route('/analisis/edit/<int:analysis_id>', methods=['GET', 'POST'])
def edit_analisis_route(analysis_id):
    item = database.get_analisis_data_by_id(analysis_id)
    if not item:
        flash('Data analisis tidak ditemukan.', 'danger')
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
    flash(f"Berita '{item_to_promote['judul_pemberitaan']}' berhasil dipromosikan.", 'success')
    return redirect(url_for('analisis'))

# ▼▼▼ RUTE BARU DITAMBAHKAN DI SINI ▼▼▼
@app.route('/analisis/promote_all_positive', methods=['POST'])
def promote_all_positive_route():
    positive_items = database.get_all_positive_analisis_data()
    promoted_count = 0
    skipped_count = 0
    for item in positive_items:
        if not database.is_pemberitaan_url_exist(item['link_pemberitaan']):
            news_data = dict(item)
            news_data['media_pemberitaan'] = "Media Online"
            news_data['kategori_media'] = "Dipromosikan dari Analisis"
            database.add_pemberitaan(news_data)
            promoted_count += 1
        else:
            skipped_count += 1
    flash(f'Berhasil mempromosikan {promoted_count} berita. {skipped_count} berita dilewati karena sudah ada.', 'success')
    return redirect(url_for('analisis'))

@app.route('/analisis/promote_selected', methods=['POST'])
def promote_selected_route():
    selected_ids = request.form.getlist('selected_ids')
    if not selected_ids:
        flash('Tidak ada berita yang dipilih.', 'warning')
        return redirect(url_for('analisis'))
    promoted_count = 0
    skipped_count = 0
    for item_id in selected_ids:
        item = database.get_analisis_data_by_id(item_id)
        if item:
            if not database.is_pemberitaan_url_exist(item['link_pemberitaan']):
                news_data = dict(item)
                news_data['media_pemberitaan'] = "Media Online"
                news_data['kategori_media'] = "Dipromosikan dari Analisis"
                database.add_pemberitaan(news_data)
                promoted_count += 1
            else:
                skipped_count += 1
    flash(f'Berhasil mempromosikan {promoted_count} berita. {skipped_count} berita dilewati karena sudah ada.', 'success')
    return redirect(url_for('analisis'))
# ▲▲▲ AKHIR DARI RUTE BARU ▲▲▲

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
    if database.is_pemberitaan_url_exist(url) or database.is_analisis_url_exist(url):
        flash('Berita dengan URL tersebut sudah ada.', 'warning')
        return redirect(url_for('pemberitaan'))
    news_data = scraper.scrape_news_data(url)
    if news_data:
        news_data['media_pemberitaan'] = media_pemberitaan
        news_data['kategori_media'] = kategori_media
        tonalitas = sentiment.analyze_title_sentiment(news_data['judul_pemberitaan'])
        news_data['sentimen'] = tonalitas
        database.add_pemberitaan(news_data)
        database.add_analisis_data(news_data)
        flash(f"Berita berhasil ditambahkan dengan sentimen '{tonalitas}'!", 'success')
    else:
        flash('Gagal mengambil data dari URL. Pastikan link valid.', 'danger')
    return redirect(url_for('pemberitaan'))

@app.route('/edit/<int:news_id>', methods=['GET', 'POST'])
def edit_news_route(news_id):
    news_item = database.get_pemberitaan_by_id(news_id)
    if not news_item:
        flash('Berita tidak ditemukan.', 'danger')
        return redirect(url_for('pemberitaan'))
    if request.method == 'POST':
        data = {
            'id': news_id, 
            'judul_pemberitaan': request.form.get('judul_pemberitaan'), 
            'kategori_media': request.form.get('kategori_media')
        }
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
    flash('Semua data berita resmi telah direset.', 'warning')
    return redirect(url_for('pemberitaan'))

@app.route('/download-excel')
def download_excel():
    conn = database.get_db_connection()
    df = pd.read_sql_query("SELECT id, tanggal, bulan, tahun, media_pemberitaan, judul_pemberitaan, link_pemberitaan, nama_media, kategori_media FROM pemberitaan_resmi", conn)
    conn.close()
    if df.empty:
        flash('Tidak ada data untuk diunduh.', 'warning')
        return redirect(url_for('pemberitaan'))
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Pemberitaan')
    output.seek(0)
    return send_file(output, as_attachment=True, download_name='laporan_pemberitaan.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

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
        flash(f"Keyword '{keyword}' berhasil ditambahkan.", "success")
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
        flash("Pemantauan manual berhasil dijalankan. Cek halaman 'Dashboard Analisis' untuk hasilnya.", "info")
    except Exception as e:
        flash(f"Terjadi error saat menjalankan pemantauan: {e}", "danger")
    return redirect(url_for('monitoring_route'))

@app.route('/monitoring/toggle', methods=['POST'])
def toggle_scheduler_route():
    job = scheduler.get_job('monitoring_job')
    if job and job.next_run_time:
        scheduler.pause_job('monitoring_job')
        flash("Scheduler pemantauan otomatis telah dihentikan.", "warning")
    elif job:
        scheduler.resume_job('monitoring_job')
        flash("Scheduler pemantauan otomatis telah dijalankan kembali.", "success")
    else:
        scheduler.add_job(run_monitoring, 'interval', minutes=60, id='monitoring_job')
        flash("Scheduler baru telah dibuat dan dijalankan.", "success")
    return redirect(url_for('monitoring_route'))

if __name__ == '__main__':
    app.run(debug=True)