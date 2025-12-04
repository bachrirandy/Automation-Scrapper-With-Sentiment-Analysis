# 📰 Automation-Scrapper-With-Sentiment-Analysis

**Web App untuk Otomatisasi Scraping Data Berita Beserta Analisis Sentimen**

Aplikasi ini memungkinkan **scraping otomatis** artikel berita *online*, *preprocessing* teks, **analisis sentimen** (positif / netral / negatif), dan penyimpanan hasil ke *database* — mendukung evaluasi citra publik perusahaan secara *real-time* atau studi kasus berbasis data.

---

## 🚀 Fitur Utama

* **Scraping Otomatis:** Mengambil artikel berita dari sumber *online* (Web Scraping).
* **Preprocessing Teks:** Melakukan *cleaning* dan normalisasi teks untuk analisis.
* **Vektorisasi Teks:** Transformasi teks ke fitur numerik menggunakan **TF-IDF**.
* **Analisis Sentimen:** Klasifikasi sentimen teks menggunakan Model *Machine Learning* (**Multinomial Naive Bayes**) dengan hasil (Positif / Netral / Negatif).
* **Antarmuka Web:** *Web interface* berbasis **Flask** untuk interaksi dan tampilan hasil.
* **Penyimpanan Data:** Menyimpan hasil *scraping* dan analisis ke *database* lokal.
* **Otomatisasi/Scheduler:** Sistem dapat meng-*scrape* dan menganalisis data secara berkala (**scheduled job**).

---

## 🧰 Teknologi / Stack

| Kategori | Teknologi | Deskripsi |
| :--- | :--- | :--- |
| **Bahasa** | Python 3.x | Bahasa utama untuk pengembangan. |
| **Web Scraping** | `requests`, `BeautifulSoup`, `Selenium` (sesuai implementasi) | Pustaka untuk pengambilan data dari web. |
| **Machine Learning** | `scikit-learn` | Pustaka untuk TF-IDF Vectorizer dan model **Multinomial Naive Bayes**. |
| **Web Framework** | Flask | *Micro-framework* Python untuk aplikasi web. |
| **Database** | SQLite (atau *database* ringan lainnya) | Penyimpanan hasil analisis lokal. |
| **Otomatisasi** | *Native Scheduler* / *Job Runner* | Untuk menjalankan tugas *scraping* berkala. |
| **Front-end** | HTML, CSS | Untuk tampilan *web interface*. |

---

## 🧑‍💻 Cara Instalasi & Menjalankan (Lokal)

### 1. Clone Repository

```bash
git clone [https://github.com/](https://github.com/)<username>/Automation-Scrapper-With-Sentiment-Analysis.git
cd Automation-Scrapper-With-Sentiment-Analysis

# Untuk Linux / macOS
python3 -m venv venv
source venv/bin/activate
# Untuk Windows
python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt

python train_and_save_model.py

python app.py

python test_scraper.py
