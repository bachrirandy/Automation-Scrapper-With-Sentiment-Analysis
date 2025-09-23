import pandas as pd
import psutil
import time
import os
import csv 

# --------------------------------------------------------------------
# --- BAGIAN 1: Impor dan siapkan scraper ANDA di sini ---
# --------------------------------------------------------------------
# Impor scraper Anda dari file 'utils.py' atau definisikan di sini
# Contoh:
from utils import scraper 
# Jika scraper Anda tidak di file terpisah, cukup pastikan 
# variabel `scraper` sudah siap digunakan.
# --------------------------------------------------------------------


# --- Daftar URL (ambil dari kode Anda) ---
urls = [
    "https://intinews.co/pln-gelar-relawan-bakti-bumn-di-sumba-timur-kolaborasi-kementerian-dan-lintas-bumn-untuk-pengabdian-masyarakat/",
    "https://intinews.co/tempati-kantor-baru-pln-up3-ogan-ilir-siap-tingkatkan-kualitas-layanan-kepada-masyarakat/",
    "https://intinews.co/listrik-tanpa-kedip-pln-uid-s2jb-sukses-kawal-keandalan-listrik-pertandingan-voli-proliga-2025-di-palembang/",
    "https://intinews.co/sinergi-pln-dan-polri-perkuat-pengamanan-objek-vital-nasional-demi-layanan-listrik-aman-dan-berkualitas/",
    "https://intinews.co/pln-bengkulu-perkuat-keandalan-listrik-jelang-bulan-suci-ramadhan-1446-h/",
    "https://intinews.co/bm-pln-up3-lahat-tuntaskan-program-senyum-sehat-untuk-masa-depan-anak-indonesia/",
    "https://indomerdeka.com/2025/02/25/pln-uid-s2jb-ajak-masyarakat-amankan-token-listrik-dukung-kenyamanan-ibadah-ramadhan/",
    "https://indomerdeka.com/2025/02/25/raih-posisi-tiga-klasemen-jakarta-electric-pln-amankan-tiket-final-four-pln-mobile-proliga-2025/",
    "https://rri.co.id/palembang/stunting/1346141/program-senyum-sehat-anak-indonesia-pln-cegah-stunting",
    "https://rri.co.id/palembang/daerah/1345904/pln-polresta-sinergi-jaga-objek-vital-nasional",
    "https://rri.co.id/palembang/daerah/1345846/pln-uid-s2jb-sukses-jaga-keandalan-listrik-proliga",
    "https://lintaswaranews.co/2025/02/25/pln-ajak-pelanggan-catat-meter-mandiri-untuk-kelola-pengeluaran-listrik/",
    "https://indoparlemenews.co/menjelang-ramadhan-pln-ingatkan-pentingnya-catat-meter-mandiri/",
    "https://saungnews.co/2025/02/pln-berikan-tips-mengelola-konsumsi-listrik-saat-ramadhan/",
    "https://sumselnews.co.id/catat-meter-mandiri-cara-pln-bantu-pelanggan-kelola-pengeluaran-listrik/#google_vignette",
    "https://indomerdeka.com/2025/02/25/ybm-pln-jambi-berbagi-kebahagiaan-jelang-ramadhan-di-rumah-asuhan-umi-ikhlas-dan-yayasan-teratai-jaya/",
    "https://sumselnews.co.id/pln-imbau-masyarakat-persiapkan-token-listrik-sebelum-ramadhan/",
    "https://saungnews.co/2025/02/pln-pastikan-ketersediaan-listrik-yang-andal-selama-ramadhan/",
    "https://indoparlemenews.co/ramadhan-nyaman-dengan-listrik-yang-andal-pln-ajak-masyarakat-beli-token-listrik-di-awal-bulan/",
    "https://lintaswaranews.co/2025/02/25/pln-berikan-tips-mengelola-konsumsi-listrik-saat-ramadhan/",
    "https://lintaswaranews.co/2025/02/25/jakarta-electric-pln-pastikan-tiket-ke-final-four-pln-mobile-proliga-2025/",
    "https://indoparlemenews.co/jakarta-electric-pln-tampil-luar-biasa-gilas-bandung-bjb-tandamata-3-0/",
    "https://extranews.id/ybm-pln-jambi-berbagi-kebahagiaan-jelang-ramadhan-di-rumah-asuhan-umi-ikhlas-dan-yayasan-teratai-jaya/",
    "https://extranews.id/pln-uid-s2jb-ajak-masyarakat-amankan-token-listrik-dukung-kenyamanan-ibadah-ramadhan/",
    "https://extranews.id/raih-posisi-tiga-klasemen-jakarta-electric-pln-amankan-tiket-final-four-pln-mobile-proliga-2025/",
    "https://saungnews.co/2025/02/jakarta-electric-pln-siap-hadapi-final-four-setelah-kalahkan-bandung-bjb-tandamata/",
    "https://sumselnews.co.id/pln-mobile-proliga-2025-jakarta-electric-pln-pastikan-tempat-di-final-four/",
    "https://www.sumsel24.com/daerah/32814631689/dukung-kenyamanan-beribadah-selama-ramadhan-pln-uid-s2jb-ajak-masyarakat-amankan-token-listrik",
    "https://beritapress.id/hancurkan-bandung-bjb-tandamata-jakarta-electric-pln-amankan-tiket-final-four/",
    "https://beritapress.id/ramadhan-tanpa-listrik-pln-ingatkan-masyarakat-segera-amankan-token/",
    "https://beritapress.id/cahaya-kebaikan-ybm-pln-jambi-santuni-yatim-dan-disabilitas-sambut-ramadhan/",
    "https://trikpos.com/jambi/ybm-pln-jambi-berbagi-kebahagiaan-jelang-ramadhan-di-rumah-asuhan-umi-ikhlas-dan-yayasan-teratai-jaya/",
    "https://trikpos.com/olahraga/raih-posisi-tiga-klasemen-jakarta-electric-pln-amankan-tiket-final-four-pln-mobile-proliga-2025/",
    "https://trikpos.com/palembang/pln-uid-s2jb-ajak-masyarakat-amankan-token-listrik-dukung-kenyamanan-ibadah-ramadhan/",
    "https://trikpos.com/pln/tips-budget-listrik-aman-selama-ramadhan-catat-meter-listrik-pascabayar-dan-dapatkan-estimasi-tagihan/",
    "https://trikpos.com/lahat/jelang-ramadhan-ybm-pln-up3-lahat-tuntaskan-program-senyum-sehat-untuk-masa-depan-anak-indonesia/",
    "https://trikpos.com/bengkulu/kolaborasi-apik-pln-bengkulu-perkuat-keandalan-listrik-jelang-bulan-suci-ramadhan-1446-h/",
    "https://trikpos.com/palembang/sinergi-pln-dan-polri-perkuat-pengamanan-objek-vital-nasional-demi-layanan-listrik-aman-dan-berkualitas/",
    "https://intinews.co/ybm-pln-jambi-berbagi-kebahagiaan-jelang-ramadhan-di-rumah-asuhan-umi-ikhlas-dan-yayasan-teratai-jaya/",
    "https://lintaswaranews.co/2025/02/25/pln-berbagi-kebahagiaan-dengan-anak-yatim-dan-penyandang-disabilitas-di-jambi/",
    "https://indoparlemenews.co/ybm-pln-up3-jambi-gelar-aksi-sosial-menjelang-ramadhan/",
    "https://saungnews.co/2025/02/pln-salurkan-bantuan-sembako-kepada-anak-yatim-dan-penyandang-disabilitas-di-jambi/",
    "https://sumselnews.co.id/berbagi-kebahagiaan-pln-up3-jambi-bantu-anak-yatim-dan-penyandang-disabilitas/",
    "https://intinews.co/tips-budget-listrik-aman-selama-ramadhan-catat-meter-listrik-pascabayar-dan-dapatkan-estimasi-tagihan/",
    "https://intinews.co/ybm-pln-jambi-berbagi-kebahagiaan-jelang-ramadhan-di-rumah-asuhan-umi-ikhlas-dan-yayasan-teratai-jaya/",
    "https://intinews.co/raih-posisi-tiga-klasemen-jakarta-electric-pln-amankan-tiket-final-four-pln-mobile-proliga-2025/",
    "https://intinews.co/pln-bengkulu-perkuat-keandalan-listrik-jelang-bulan-suci-ramadhan-1446-h/",
    "https://sumsel.akurat.co/nasional/1865696547/berkah-ramadhan-pln-beri-diskon-50-persen-tambah-daya-listrik",
    "https://indoparlemenews.co/pln-hadirkan-promo-menyambut-ramadan-diskon-tambah-daya-50/",
    "https://sumselnews.co.id/diskon-50-untuk-tambah-daya-listrik-pln-sambut-ramadan-2025/",
    "https://saungnews.co/2025/02/pln-beri-diskon-50-untuk-tambah-daya-listrik-di-bulan-ramadan/",
    "https://wideazone.com/promo-ramadan-pln-diskon-tambah-daya-50-plus-50/",
    "https://lintaswaranews.co/2025/02/28/menyambut-ramadan-pln-tawarkan-diskon-tambah-daya-listrik-hingga-50/",
    "https://indomerdeka.com/2025/02/28/promo-ramadan-dari-pln-diskon-tambah-daya-50-50-begini-penjelasannya/",
    "https://extranews.id/promo-ramadan-dari-pln-diskon-tambah-daya-50-50-begini-penjelasannya/",
    "https://intinews.co/promo-ramadan-diskon-tambah-daya-50-50-begini-penjelasannya/",
    "https://wawberita.com/2025/03/01/promo-ramadan-dari-pln-diskon-tambah-daya-50-50-begini-penjelasannya/",
    "https://www.sumsel24.com/nasional/32814663609/promo-ramadan-dari-pln-diskon-tambah-daya-50-persen-plus-50-persen-begini-penjelasannya",
    "https://indomerdeka.com/2025/03/02/pln-up3-lubuk-linggau-beri-tips-mendukung-kenyamanan-ibadah-ramadhan/",
    "https://kabarmegapolitan.pikiran-rakyat.com/nasional/pr-1749116226/pln-bayar-tagihan-listrik-tepat-waktu-untuk-ibadah-ramadan-yang-khusyuk",
    "https://beritapress.id/pln-up3-lubuk-linggau-beri-tips-untuk-kenyamanan-ibadah-ramadan/",
    "https://extranews.id/pln-up3-lubuk-linggau-beri-tips-mendukung-kenyamanan-ibadah-ramadhan/",
    "https://intinews.co/pln-up3-lubuk-linggau-ajak-pelanggan-dukung-kelancaran-ibadah-puasa-dengan-bayar-tagihan-tepat-waktu/",
    "https://indoparlemenews.co/pln-imbau-pelanggan-bayar-tagihan-listrik-tepat-waktu-di-awal-bulan/",
    "https://saungnews.co/2025/03/pln-ajak-masyarakat-bayar-tagihan-listrik-awal-bulan-untuk-dukung-kelancaran-ibadah-ramadan/",
    "https://sumselnews.co.id/bayar-tagihan-listrik-tepat-waktu-pln-minta-dukungan-masyarakat-di-awal-bulan/",
    "https://lintaswaranews.co/2025/03/02/pln-imbau-masyarakat-untuk-bayar-tagihan-listrik-awal-bulan-demi-kelancaran-ibadah-ramadan/",
    "https://haluansumatera.com/pln-up3-lubuk-linggau-beri-tips-mendukung-kenyamanan-ibadah-ramadhan/",
    "https://trikpos.com/lubuklinggau/pln-up3-lubuk-linggau-beri-tips-mendukung-kenyamanan-ibadah-ramadhan/",
    "https://trikpos.com/bumn/promo-ramadan-dari-pln-diskon-tambah-daya-50-50-begini-penjelasannya/",
    "https://sonorapalembang.com/pln-up3-lubuk-linggau-beri-tips-mendukung-kenyamanan-ibadah-ramadhan/",
    "https://rri.co.id/palembang/daerah/1362702/pln-lubuk-linggau-ajak-bayar-listrik-tepat-waktu",
    "https://indomerdeka.com/2025/03/03/tingkatkan-keandalan-pln-lakukan-pemindahan-kabel-konduktor-dari-tower-darurat-ke-tower-permanen/",
    "https://wideazone.com/kabel-konduktor-150kv-kenten-tanjung-api-api-pindah-dari-tower-darurat-ke-tower-permanen/",
    "https://trikpos.com/banyuasin/pln-lakukan-pemindahan-kabel-konduktor-dari-tower-darurat-ke-tower-permanen/",
    "https://kabarmegapolitan.pikiran-rakyat.com/nasional/pr-1749118823/amankan-pasokan-listrik-pln-pindahkan-kabel-konduktor-ke-tower-permanen",
    "https://sonorapalembang.com/tingkatkan-keandalan-pln-lakukan-pemindahan-kabel-konduktor-dari-tower-darurat-ke-tower-permanen/",
    "https://rri.co.id/palembang/daerah/1364222/pln-pindahkan-kabel-konduktor-untuk-keandalan-listrik",
    "https://indomerdeka.com/2025/03/03/pastikan-kesiapan-layanan-spklu-jelang-mudik-lebaran-direktur-retail-niaga-bersama-manajemen-pln-s2jb-inspeksi-bersama/",
    "https://www.sumsel24.com/daerah/32814676452/tingkatkan-keandalan-pln-lakukan-pemindahan-kabel-konduktor-dari-tower-darurat-ke-tower-permanen",
    "https://www.sumsel24.com/nasional/32814676673/pastikan-kesiapan-layanan-spklu-jelang-mudik-lebaran-direktur-retail-dan-niaga-bersama-manajemen-pln-s2jb-inspeksi-bersama",
    "https://beritapress.id/pln-lakukan-pemindahan-kabel-konduktor-dari-tower-darurat-ke-tower-permanen/",
    "https://beritapress.id/pln-pastikan-spklu-siap-tempur-inspeksi-besar-jelang-mudik-lebaran-2025/",
    "https://extranews.id/pastikan-kesiapan-layanan-spklu-jelang-mudik-lebaran-direktur-retail-niaga-bersama-manajemen-pln-s2jb-inspeksi-bersama/",
    "https://wawberita.com/2025/03/03/pastikan-kesiapan-layanan-spklu-jelang-mudik-lebaran-direktur-retail-niaga-bersama-manajemen-pln-s2jb-inspeksi-bersama/",
    "https://trikpos.com/pln/pastikan-kesiapan-layanan-spklu-jelang-mudik-lebaran-direktur-retail-niaga-bersama-manajemen-pln-s2jb-inspeksi-bersama/",
    "https://intinews.co/pastikan-kesiapan-layanan-spklu-jelang-mudik-lebaran-direktur-retail-niaga-bersama-manajemen-pln-s2jb-inspeksi-bersama/",
    "https://rri.co.id/palembang/daerah/1364544/pln-pastikan-kesiapan-spklu-untuk-mudik-lebaran",
    "https://indomerdeka.com/2025/03/04/pln-up3-lahat-perbaiki-jaringan-listrik-sambut-ramadhan-pastikan-ibadah-masyarakat-nyaman/",
    "https://updatekini.com/pln-up3-lahat-perbaiki-jaringan-listrik-sambut-ramadan/",
    "https://beritapress.id/pln-lahat-berjuang-lawan-penyulang-sakit-pastikan-ramadhan-tanpa-pemadaman/",
    "https://sonorapalembang.com/pln-up3-lahat-perbaiki-jaringan-listrik-sambut-ramadhan-pastikan-ibadah-masyarakat-nyaman/",
    "https://trikpos.com/lahat/tuntaskan-gangguan-pln-up3-lahat-perbaiki-jaringan-listrik-sambut-ramadhan/",
    "https://extranews.id/pln-up3-lahat-perbaiki-jaringan-listrik-sambut-ramadhan-pastikan-ibadah-masyarakat-nyaman/",
    "https://updatekini.com/pln-suplai-listrik-hijau-ke-pt-inecda-plantation-serap-592-unit-rec/",
    "https://bisnissumsel.com/pln-uid-s2jb-ajak-masyarakat-amankan-token-listrik-dukung-kenyamanan-ibadah-ramadhan/",
    "https://bisnissumsel.com/raih-posisi-tiga-klasemen-jakarta-electric-pln-amankan-tiket-final-four-pln-mobile-proliga-2025/",
    "https://rakyatpembaruan.com/pln-uid-s2jb-ajak-masyarakat-amankan-token-listrik-dukung-kenyamanan-ibadah-ramadhan/",
    "https://rakyatpembaruan.com/raih-posisi-tiga-klasemen-jakarta-electric-pln-amankan-tiket-final-four-pln-mobile-proliga-2025/",
    "https://rakyatpembaruan.com/pln-uid-s2jb-ajak-masyarakat-amankan-token-listrik-dukung-kenyamanan-ibadah-ramadhan/"
]

# List untuk menyimpan semua hasil
hasil_data = []

# Mendapatkan proses Python saat ini untuk monitoring
proses_saat_ini = psutil.Process(os.getpid())

print("Memulai proses scraping dengan monitoring sumber daya...")

# --- Proses Scraping ---
for url in urls:
    try:
        # 1. Catat penggunaan sumber daya SEBELUM request
        cpu_usage = proses_saat_ini.cpu_percent(interval=0.1)
        memory_info = proses_saat_ini.memory_info()
        memory_usage_mb = memory_info.rss / (1024 * 1024)

        # Catat waktu mulai
        start_time = time.time()

        # --------------------------------------------------------------------
        # --- BAGIAN 2: Panggil scraper ANDA di sini ---
        # --------------------------------------------------------------------
        # Ini adalah bagian terpenting. Gunakan pemanggilan scraper asli Anda.
        data = scraper.scrape_news_data(url)
        # --------------------------------------------------------------------
        
        # Catat waktu selesai
        end_time = time.time()
        latency = end_time - start_time

        # Menentukan status dan judul dari hasil scraper Anda
        if data and data.get('judul_pemberitaan'):
            status = 'Berhasil'
            status_code = 200 # Asumsikan 200 jika berhasil
        else:
            status = 'Gagal'
            status_code = 'N/A'
        
        print(f"URL: {url[:50]}... | Status: {status} | Latency: {latency:.2f} detik")

    except Exception as e:
        # Tangani jika terjadi error pada scraper Anda atau koneksi
        latency = time.time() - start_time
        status = f'Gagal (Error: {e})'
        status_code = 'N/A'
        print(f"URL: {url[:50]}... | Status: {status}")

    # 4. Tambahkan semua data ke list hasil
    hasil_data.append({
        'URL': url,
        'Status_Code': status_code,
        'Status': status,
        'Waktu_Respon_detik': latency,
        'CPU_Usage_persen': cpu_usage,
        'Memory_Usage_MB': memory_usage_mb
    })
    
    time.sleep(1)

print("\nProses scraping selesai.")

# --- Simpan Hasil ---
df_hasil = pd.DataFrame(hasil_data)
nama_file_output = 'hasil_scraping_sumberdaya.csv'
df_hasil.to_csv(nama_file_output, index=False)

print(f"\nData berhasil disimpan ke file: {nama_file_output}")
print(df_hasil.head())