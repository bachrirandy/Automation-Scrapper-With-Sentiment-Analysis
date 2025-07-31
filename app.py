import io
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from datetime import datetime, timedelta
import feedparser
from urllib.parse import quote, urlparse
import re
import time
import os

# Import Selenium untuk menangani redirect link Google News
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

from config import Config
from utils import database, scraper, sentiment

app = Flask(__name__)
app.config.from_object(Config)

# Inisialisasi database
with app.app_context():
    database.init_db()

# --- ROUTES ---

@app.route('/')
def home():
    return render_template('dashboard/home.html')

# --- Rute untuk Dashboard Analisis ---
@app.route('/analisis')
def analisis():
    sentiment_filter = request.args.get('filter', None)
    conn = database.get_db_connection()
    try:
        # Ambil semua data sekali saja untuk efisiensi
        all_data_query = "SELECT * FROM analisis_data"
        full_df = pd.read_sql_query(all_data_query, conn)
    except pd.io.sql.DatabaseError:
        full_df = pd.DataFrame()
    finally:
        conn.close()

    total_berita = len(full_df)
    positif_count, negatif_count, netral_count = 0, 0, 0
    if not full_df.empty and 'sentimen' in full_df.columns:
        sentimen_counts_total = full_df['sentimen'].value_counts()
        positif_count = int(sentimen_counts_total.get('Positif', 0))
        negatif_count = int(sentimen_counts_total.get('Negatif', 0))
        netral_count = int(sentimen_counts_total.get('Netral', 0))

    # Data untuk Pie Chart dan Tabel (ini yang difilter)
    if sentiment_filter and not full_df.empty:
        df_for_display = full_df[full_df['sentimen'] == sentiment_filter].copy()
        analysis_list = database.get_filtered_analisis_data(sentiment_filter)
    else:
        df_for_display = full_df.copy()
        # ▼▼▼ PERBAIKAN DI SINI ▼▼▼
        analysis_list = database.get_filtered_analisis_data() # Panggil fungsi yang benar
        # ▲▲▲ AKHIR PERBAIKAN ▲▲▲

    sentimen_labels, sentimen_data, sentimen_colors = [], [], []
    color_map = {'Positif': '#198754', 'Negatif': '#dc3545', 'Netral': '#6c757d'}
    if not df_for_display.empty and 'sentimen' in df_for_display.columns:
        sentimen_counts_chart = df_for_display['sentimen'].value_counts()
        sentimen_labels = sentimen_counts_chart.index.tolist()
        sentimen_data = sentimen_counts_chart.values.tolist()
        sentimen_colors = [color_map.get(label, '#CCCCCC') for label in sentimen_labels]
    
    # Logika tren 7 hari terakhir SEKARANG SELALU MENGGUNAKAN DATA LENGKAP (full_df)
    trend_labels, trend_positif, trend_negatif, trend_netral = [], [], [], []
    if not full_df.empty and 'tanggal' in full_df.columns:
        df_for_trend = full_df.copy()
        df_for_trend['tanggal_lengkap'] = pd.to_datetime(df_for_trend['tahun'].astype(str) + '-' + df_for_trend['bulan'].astype(str) + '-' + df_for_trend['tanggal'].astype(str), errors='coerce')
        df_for_trend.dropna(subset=['tanggal_lengkap'], inplace=True)
        
        if not df_for_trend.empty:
            seven_days_ago = datetime.now() - timedelta(days=7)
            df_last_7_days = df_for_trend[df_for_trend['tanggal_lengkap'] >= seven_days_ago]
            
            if not df_last_7_days.empty:
                sentiment_trend = df_last_7_days.groupby([df_last_7_days['tanggal_lengkap'].dt.date, 'sentimen']).size().unstack(fill_value=0).reindex(columns=['Positif', 'Negatif', 'Netral'], fill_value=0)
                
                date_range = pd.date_range(end=datetime.now().date(), periods=7)
                sentiment_trend.index = pd.to_datetime(sentiment_trend.index)
                sentiment_trend = sentiment_trend.reindex(date_range, fill_value=0)

                trend_labels = [d.strftime('%b %d') for d in sentiment_trend.index]
                trend_positif = sentiment_trend['Positif'].tolist()
                trend_negatif = sentiment_trend['Negatif'].tolist()
                trend_netral = sentiment_trend['Netral'].tolist()

    return render_template(
        'analisis/analisis.html',
        total_berita=total_berita, positif_count=positif_count, negatif_count=negatif_count, netral_count=netral_count,
        sentimen_labels=sentimen_labels, sentimen_data=sentimen_data, sentimen_colors=sentimen_colors,
        analysis_list=analysis_list, active_filter=sentiment_filter,
        latest_news=database.get_latest_analisis_data(5),
        trend_labels=trend_labels,
        trend_positif_data=trend_positif,
        trend_negatif_data=trend_negatif,
        trend_netral_data=trend_netral
    )

@app.route('/analisis/cek_manual', methods=['POST'])
def cek_sentimen_manual():
    user_input = request.form.get('user_input')
    if not user_input:
        flash('Input tidak boleh kosong.', 'warning')
        return redirect(url_for('analisis'))

    news_data = scraper.scrape_news_data(user_input)
    
    if not news_data:
        flash('Gagal mengambil data dari URL atau input tidak valid.', 'danger')
        return redirect(url_for('analisis'))

    if "manual_input" not in news_data['link_pemberitaan']:
        if database.is_analisis_url_exist(news_data['link_pemberitaan']) or database.is_pemberitaan_url_exist(news_data['link_pemberitaan']):
            flash('Berita dari link ini sudah ada di dalam database.', 'warning')
            return redirect(url_for('analisis'))

    hasil_sentimen = sentiment.analyze_title_sentiment(news_data['judul_pemberitaan'])
    news_data['sentimen'] = hasil_sentimen
    database.add_analisis_data(news_data)
    flash(f"Judul berhasil dianalisis dan disimpan dengan sentimen: {hasil_sentimen}", "success")
    return redirect(url_for('analisis'))

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
    news_data['kategori_media'] = "Belum Dikategorikan"
    database.add_pemberitaan(news_data)
    flash(f"Berita '{item_to_promote['judul_pemberitaan']}' berhasil dipromosikan.", 'success')
    return redirect(url_for('analisis'))

@app.route('/analisis/promote_all_positive', methods=['POST'])
def promote_all_positive_route():
    positive_items = database.get_all_positive_analisis_data()
    promoted_count, skipped_count = 0, 0
    for item in positive_items:
        if not database.is_pemberitaan_url_exist(item['link_pemberitaan']):
            news_data = dict(item)
            news_data['media_pemberitaan'] = "Media Online"
            news_data['kategori_media'] = "Belum Dikategorikan"
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
    promoted_count, skipped_count = 0, 0
    for item_id in selected_ids:
        item = database.get_analisis_data_by_id(item_id)
        if item:
            if not database.is_pemberitaan_url_exist(item['link_pemberitaan']):
                news_data = dict(item)
                news_data['media_pemberitaan'] = "Media Online"
                news_data['kategori_media'] = "Belum Dikategorikan"
                database.add_pemberitaan(news_data)
                promoted_count += 1
            else:
                skipped_count += 1
    flash(f'Berhasil mempromosikan {promoted_count} berita. {skipped_count} berita dilewati karena sudah ada.', 'success')
    return redirect(url_for('analisis'))

# --- Rute untuk Data Pemberitaan ---
@app.route('/pemberitaan')
def pemberitaan():
    news_list = database.get_all_pemberitaan()
    return render_template('berita/pemberitaan.html', news_list=news_list)

@app.route('/add', methods=['POST'])
def add_news_route():
    url = request.form.get('url')
    if not url:
        flash('URL tidak boleh kosong!', 'danger')
        return redirect(url_for('pemberitaan'))
    if database.is_pemberitaan_url_exist(url):
        flash('Berita dengan URL tersebut sudah ada di tabel pemberitaan.', 'warning')
        return redirect(url_for('pemberitaan'))
    
    news_data = scraper.scrape_news_data(url)
    
    if news_data:
        news_data['media_pemberitaan'] = request.form.get('media_pemberitaan')
        news_data['kategori_media'] = request.form.get('kategori_media')
        database.add_pemberitaan(news_data)
        flash("Berita berhasil ditambahkan ke Data Pemberitaan.", 'success')
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
            'nama_media': request.form.get('nama_media'),
            'tanggal': request.form.get('tanggal'),
            'bulan': request.form.get('bulan'),
            'tahun': request.form.get('tahun'),
            'media_pemberitaan': request.form.get('media_pemberitaan'),
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
    return send_file(output, as_attachment=True, download_name='laporan_pemberitaan.xlsx')

# --- Rute untuk Fitur Cari Berita ---
@app.route('/cari-berita', methods=['GET'])
def cari_berita():
    hasil = database.get_all_hasil_pencarian()
    return render_template('dashboard/cari_berita.html', hasil_pencarian=hasil)

@app.route('/cari-berita/run', methods=['POST'])
def run_pencarian_berita():
    keywords_input = request.form.get('keywords')
    limit = int(request.form.get('limit', 25)) 

    if not keywords_input:
        flash('Keyword pencarian tidak boleh kosong.', 'warning')
        return redirect(url_for('cari_berita'))

    keywords_list = [k.strip() for k in re.split(r'[,\n]', keywords_input) if k.strip()]
    database.clear_hasil_pencarian()
    
    all_entries = []
    unique_links = set()

    for keyword in keywords_list:
        search_term = quote(keyword)
        source_url = f"https://news.google.com/rss/search?q={search_term}&hl=id&gl=ID&ceid=ID:id"
        feed = feedparser.parse(source_url)
        for entry in feed.entries:
            if entry.link not in unique_links:
                all_entries.append(entry)
                unique_links.add(entry.link)

    found_count = 0
    
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--log-level=3')
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    driver = None

    try:
        driver_path = os.path.join(os.getcwd(), 'chromedriver.exe')
        if not os.path.exists(driver_path):
            flash("Error: chromedriver.exe tidak ditemukan.", "danger")
            return redirect(url_for('cari_berita'))
        
        service = ChromeService(executable_path=driver_path)
        driver = webdriver.Chrome(service=service, options=options)
        
        entries_to_process = all_entries[:limit]

        for entry in entries_to_process:
            try:
                google_link = entry.link
                driver.get(google_link)
                time.sleep(0.5) 
                real_link = driver.current_url

                if "news.google.com" in urlparse(real_link).netloc:
                    continue

                news_item = {
                    'judul_pemberitaan': entry.title,
                    'link_pemberitaan': real_link,
                    'nama_media': urlparse(real_link).netloc.replace('www.', '')
                }
                database.add_hasil_pencarian(news_item)
                found_count += 1
            except Exception as e:
                print(f"Gagal memproses link: {entry.link}. Error: {e}")
                continue
    finally:
        if driver:
            driver.quit()
    
    flash(f"{found_count} berita ditemukan dari keyword yang Anda masukkan.", "success")
    return redirect(url_for('cari_berita'))

@app.route('/cari-berita/reset', methods=['POST'])
def reset_pencarian_route():
    """Menghapus semua hasil pencarian dari tabel sementara."""
    database.clear_hasil_pencarian()
    flash('Hasil pencarian berhasil direset.', 'info')
    return redirect(url_for('cari_berita'))

@app.route('/analisis/terpilih', methods=['POST'])
def analisis_berita_terpilih():
    selected_links = request.form.getlist('selected_links')
    if not selected_links:
        flash("Tidak ada berita yang dipilih untuk dianalisis.", "warning")
        return redirect(url_for('cari_berita'))

    analyzed_count = 0
    skipped_count = 0
    for link in selected_links:
        if database.is_analisis_url_exist(link) or database.is_pemberitaan_url_exist(link):
            skipped_count += 1
            continue
        
        news_data = scraper.scrape_news_data(link)
        
        if news_data:
            hasil_sentimen = sentiment.analyze_title_sentiment(news_data['judul_pemberitaan'])
            news_data['sentimen'] = hasil_sentimen
            database.add_analisis_data(news_data)
            analyzed_count += 1
    
    flash(f"{analyzed_count} berita berhasil dianalisis dan disimpan. {skipped_count} berita dilewati.", "success")
    return redirect(url_for('analisis'))

if __name__ == '__main__':
    app.run(debug=True)