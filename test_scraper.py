from requests_html import HTMLSession

print("--- MEMULAI TES SCRAPER ---")
session = HTMLSession()
url = 'https://www.detik.com/' # Menggunakan link yang umum

print(f"Mencoba mengakses: {url}")

try:
    r = session.get(url, timeout=30)
    print(f"Status Kode: {r.status_code}")
    print("Mencoba me-render JavaScript (langkah ini yang sering gagal)...")
    
    # Proses render ini akan memicu download Chromium jika belum ada
    r.html.render(sleep=3, timeout=40)
    
    judul = r.html.find('title', first=True)
    if judul:
        print(f"Render berhasil. Judul halaman: {judul.text}")
        print("\n✅ Scraper dasar BERHASIL dijalankan!")
    else:
        print("\n❌ Render selesai, TAPI judul tidak ditemukan.")

except Exception as e:
    print("\n❌❌❌ TERJADI ERROR ❌❌❌")
    print(f"Error: {e}")

print("--- TES SELESAI ---")