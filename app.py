import io
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from datetime import datetime, timedelta
import feedparser
from urllib.parse import quote, urlparse
import time

# Selenium untuk menangani redirect link Google News
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
    """Rute untuk halaman selamat datang."""
    return render_template('dashboard/home.html')

# --- Rute untuk Dashboard Analisis ---
@app.route('/analisis')
def analisis():
    """Rute untuk dasbor statistik sentimen."""
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

    news_data = {}
    judul_untuk_dianalisis = ""

    if user_input.strip().startswith(('http://', 'https://')):
        link = user_input.strip()
        if database.is_analisis_url_exist(link) or database.is_pemberitaan_url_exist(link):
            flash('Berita dari link ini sudah ada di dalam database.', 'warning')
            return redirect(url_for('analisis'))
        
        scraped_data = scraper.scrape_news_data(link)
        if scraped_data:
            news_data = scraped_data
            judul_untuk_dianalisis = news_data.get('judul_pemberitaan')
        else:
            flash('Gagal mengambil data dari link yang diberikan.', 'danger')
            return redirect(url_for('analisis'))
    else:
        judul_untuk_dianalisis = user_input
        news_data = {
            "tanggal": datetime.now().day,
            "bulan": datetime.now().month,
            "tahun": datetime.now().year,
            "judul_pemberitaan": judul_untuk_dianalisis,
            "link_pemberitaan": f"manual_input_{datetime.now().timestamp()}",
            "nama_media": "Input Manual",
        }

    hasil_sentimen = sentiment.analyze_title_sentiment(judul_untuk_dianalisis)
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
    news_data['kategori_media'] = "Dipromosikan dari Analisis"
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
    promoted_count, skipped_count = 0, 0
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

# --- Rute untuk Data Pemberitaan ---
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
    return send_file(output, as_attachment=True, download_name='laporan_pemberitaan.xlsx')

# --- Rute untuk Fitur Cari Berita ---
@app.route('/cari-berita', methods=['GET'])
def halaman_pencarian():
    """Menampilkan halaman pencarian dan hasilnya."""
    hasil = database.get_all_hasil_pencarian()
    return render_template('dashboard/cari_berita.html', hasil_pencarian=hasil)

@app.route('/cari-berita/run', methods=['POST'])
def run_pencarian_berita():
    """Menjalankan proses pencarian berdasarkan keyword."""
    keyword = request.form.get('keyword')
    if not keyword:
        flash('Keyword pencarian tidak boleh kosong.', 'warning')
        return redirect(url_for('halaman_pencarian'))

    database.clear_hasil_pencarian()

    search_term = quote(keyword)
    source_url = f"https://news.google.com/rss/search?q={search_term}&hl=id&gl=ID&ceid=ID:id"
    feed = feedparser.parse(source_url)
    
    found_count = 0
    
    # Setup Selenium options
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--log-level=3')
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    driver = None

    try:
        # Initialize WebDriver
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        for entry in feed.entries:
            try:
                google_link = entry.link
                
                # Use Selenium to get the final URL
                driver.get(google_link)
                time.sleep(0.5) 
                real_link = driver.current_url

                # Fallback check: if it's still a google link, skip it
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
    
    flash(f"{found_count} berita ditemukan untuk keyword '{keyword}'.", "success")
    return redirect(url_for('halaman_pencarian'))

@app.route('/analisis/terpilih', methods=['POST'])
def analisis_berita_terpilih():
    """Mengambil berita terpilih dari hasil pencarian untuk dianalisis."""
    selected_links = request.form.getlist('selected_links')
    if not selected_links:
        flash("Tidak ada berita yang dipilih untuk dianalisis.", "warning")
        return redirect(url_for('halaman_pencarian'))

    analyzed_count = 0
    skipped_count = 0
    for link in selected_links:
        if database.is_analisis_url_exist(link) or database.is_pemberitaan_url_exist(link):
            skipped_count += 1
            continue
        
        item_pencarian = database.get_pencarian_by_link(link)
        if not item_pencarian:
            continue

        news_data = {
            "tanggal": datetime.now().day,
            "bulan": datetime.now().month,
            "tahun": datetime.now().year,
            "judul_pemberitaan": item_pencarian['judul_berita'],
            "link_pemberitaan": item_pencarian['link_pemberitaan'],
            "nama_media": item_pencarian['nama_media'],
        }
        
        hasil_sentimen = sentiment.analyze_title_sentiment(news_data['judul_pemberitaan'])
        news_data['sentimen'] = hasil_sentimen
        
        database.add_analisis_data(news_data)
        analyzed_count += 1
    
    flash(f"{analyzed_count} berita berhasil dianalisis dan disimpan. {skipped_count} berita dilewati karena sudah ada.", "success")
    return redirect(url_for('analisis'))

if __name__ == '__main__':
    app.run(debug=True)
