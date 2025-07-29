# Nama File: utils/sentiment.py
# Lokasi: C:\HIKMAH MAHARANI\KERJA PRAKTIK\NLP PROJECT\Automation-Scrapper-With-Sentiment-Analysis\utils\sentiment.py

import pickle
import re
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from scipy.sparse import hstack # Import untuk menggabungkan fitur saat prediksi


# --- Inisialisasi dan Muat Model ---
model = None
vectorizer = None
try:
    with open('utils/sentiment_model.pkl', 'rb') as model_file:
        model = pickle.load(model_file)
    with open('utils/tfidf_vectorizer.pkl', 'rb') as vec_file:
        vectorizer = pickle.load(vec_file)
    print("--- SENTIMENT: Model dan vectorizer berhasil dimuat. ---")
except FileNotFoundError:
    print("--- SENTIMENT ERROR: File model atau vectorizer tidak ditemukan. Pastikan sudah melatih dan menyimpannya di folder 'utils'. ---")
    print("--- SENTIMENT: Menggunakan fallback 'Netral' untuk prediksi sentimen. ---")
except Exception as e:
    print(f"--- SENTIMENT ERROR: Gagal memuat model: {e} ---")
    print("--- SENTIMENT: Menggunakan fallback 'Netral' untuk prediksi sentimen. ---")

# === DEFINISI GLOBAL UNTUK FEATURE ENGINEERING (HARUS SAMA DI TRAIN_AND_SAVE_MODEL.PY) ===
positive_context_words = ['mudah', 'aplikasi', 'akurat', 'bantu', 'solusi', 'inovasi', 'baik', 'normal', 'pulih', 'cek', 'sekitar']
negative_core_words = ['padam', 'listrik', 'ganggu', 'keluh', 'rusak', 'mati', 'buruk', 'turun']
# =======================================================================================


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
    custom_stopwords = ['pln', 's2jb', 'uid', 'karena', 'akibat', 'sehingga', 'yakni', 'yaitu', 'terhadap', 'adalah', 'merupakan']
    
    # === PERBAIKAN: Definisi all_stopwords dipindahkan ke dalam fungsi ===
    all_stopwords = set(list_stopwords_sastrawi + list_stopwords_nltk + custom_stopwords)
    
    tokens = [word for word in tokens if word not in all_stopwords]

    stem_factory = StemmerFactory()
    stemmer = stem_factory.create_stemmer()
    tokens = [stemmer.stem(word) for word in tokens]
    return " ".join(tokens)

# --- Fungsi Utama untuk Analisis Sentimen ---
def analyze_title_sentiment(text):
    if model is None or vectorizer is None:
        return "Netral"

    clean_text = preprocess_text(text)

    if not clean_text.strip():
        return "Netral"
    
    # === FEATURE ENGINEERING SAMA DENGAN SAAT PELATIHAN ===
    clean_text_tokens = clean_text.split()
    has_negative_trigger = any(word in clean_text_tokens for word in negative_core_words)
    has_positive_context_trigger = any(word in clean_text_tokens for word in positive_context_words)
    feature_value = 1 if has_negative_trigger and has_positive_context_trigger else 0
    # ======================================================

    try:
        text_vector = vectorizer.transform([clean_text])
        
        # === GABUNGKAN FITUR TEKS DENGAN FITUR BARU ===
        # Perhatikan [[feature_value]] untuk membuat array 2D yang benar
        final_input_vector = hstack([text_vector, [[feature_value]]]) 
        
        prediction_label = model.predict(final_input_vector)[0]

        if prediction_label == 0:
            return "Negatif"
        elif prediction_label == 1:
            return "Netral"
        elif prediction_label == 2:
            return "Positif"
        else:
            return "Netral"

    except Exception as e:
        print(f"--- SENTIMENT ERROR: Terjadi error saat memprediksi sentimen: {e} ---")
        return "Netral"