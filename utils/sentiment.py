# Nama File: utils/sentiment.py
# Lokasi: C:\HIKMAH MAHARANI\KERJA PRAKTIK\NLP PROJECT\Automation-Scrapper-With-Sentiment-Analysis\utils\sentiment.py

import pickle
import re
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
# Tidak ada import `sklearn.preprocessing.LabelEncoder` di sini
# Karena kita tidak melatih encoder di sini, hanya memprediksi.

# --- Inisialisasi dan Muat Model ---
# Variabel global untuk model dan vectorizer, akan dimuat sekali saat aplikasi dimulai
model = None
vectorizer = None

try:
    # Memuat model dan vectorizer dari file .pkl
    # Path relatif terhadap lokasi `app.py` saat dijalankan `flask run`
    with open('utils/sentiment_model.pkl', 'rb') as model_file:
        model = pickle.load(model_file)
    with open('utils/tfidf_vectorizer.pkl', 'rb') as vec_file:
        vectorizer = pickle.load(vec_file)
    print("--- SENTIMENT: Model dan vectorizer berhasil dimuat. ---")
except FileNotFoundError:
    print("--- SENTIMENT ERROR: File model atau vectorizer tidak ditemukan. Pastikan sudah melatihnya. ---")
    print("--- SENTIMENT: Menggunakan fallback 'Netral' untuk prediksi sentimen. ---")
except Exception as e:
    print(f"--- SENTIMENT ERROR: Gagal memuat model: {e} ---")
    print("--- SENTIMENT: Menggunakan fallback 'Netral' untuk prediksi sentimen. ---")

# --- Fungsi Pra-pemrosesan Teks (Harus sama persis dengan saat pelatihan) ---
def preprocess_text(text):
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    tokens = word_tokenize(text)

    stop_factory = StopWordRemoverFactory()
    list_stopwords_sastrawi = stop_factory.get_stop_words()
    list_stopwords_nltk = stopwords.words('indonesian')
    # === PENTING: Gunakan stopword kustom yang sama persis dengan saat pelatihan ===
    custom_stopwords = ['padam', 'listrik', 'pln', 's2jb', 'uid', 'ganggu', 'layanan', 'warga', 'karena', 'akibat']
    all_stopwords = set(list_stopwords_sastrawi + list_stopwords_nltk + custom_stopwords)
    tokens = [word for word in tokens if word not in all_stopwords]

    stem_factory = StemmerFactory()
    stemmer = stem_factory.create_stemmer()
    tokens = [stemmer.stem(word) for word in tokens]
    return " ".join(tokens)

# --- Fungsi Utama untuk Analisis Sentimen ---
def analyze_title_sentiment(text):
    """
    Fungsi ini mengambil judul berita, mempra-prosesnya, dan mengembalikan sentimen
    menggunakan model yang sudah dimuat.
    """
    if model is None or vectorizer is None:
        # Jika model tidak berhasil dimuat, langsung kembalikan 'Netral'
        return "Netral"

    clean_text = preprocess_text(text)

    if not clean_text.strip(): # Cek jika teks kosong setelah preprocessing
        return "Netral"

    try:
        text_vector = vectorizer.transform([clean_text])
        prediction_label = model.predict(text_vector)[0]

        # === PENTING: Mapping label harus sesuai dengan hasil LabelEncoder saat pelatihan ===
        # Berdasarkan output LabelEncoder Anda sebelumnya: {0: 'negatif', 1: 'netral', 2: 'positif'}
        # Gunakan nama label awal Anda (misal: 'negatif', 'netral', 'positif')
        # Atau jika di aplikasi ingin menggunakan "Negatif", "Netral", "Positif" (huruf kapital)
        # sesuaikan di sini.
        if prediction_label == 0:
            return "Negatif" # Huruf kapital untuk tampilan di UI
        elif prediction_label == 1:
            return "Netral"  # Huruf kapital untuk tampilan di UI
        elif prediction_label == 2:
            return "Positif" # Huruf kapital untuk tampilan di UI
        else:
            return "Netral" # Fallback jika ada label yang tidak dikenali

    except Exception as e:
        print(f"--- SENTIMENT ERROR: Terjadi error saat memprediksi sentimen: {e} ---")
        return "Netral" # Fallback jika ada error saat prediksi