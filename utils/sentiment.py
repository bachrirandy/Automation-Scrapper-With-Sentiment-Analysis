# pln-news-monitor/utils/sentiment.py

import pickle
import re
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# --- Inisialisasi dan Muat Model ---
model = None
vectorizer = None
try:
    print("--- SENTIMENT: Mencoba memuat model dan vectorizer ---")
    with open('utils/sentiment_model.pkl', 'rb') as model_file:
        model = pickle.load(model_file)
    with open('utils/tfidf_vectorizer.pkl', 'rb') as vec_file:
        vectorizer = pickle.load(vec_file)
    print("--- SENTIMENT: Model dan vectorizer BERHASIL dimuat. ---")
except FileNotFoundError:
    print("\n!!!!!! SENTIMENT ERROR: File model atau vectorizer tidak ditemukan di folder 'utils'. !!!!!!\n")
except Exception as e:
    print(f"\n!!!!!! SENTIMENT ERROR: Gagal memuat model: {e} !!!!!!\n")

# --- Fungsi Preprocessing Teks (harus sama seperti saat pelatihan) ---
def preprocess_text(text):
    if not isinstance(text, str): 
        return "" 
    text = text.lower()
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    tokens = word_tokenize(text)

    list_stopwords_sastrawi = StopWordRemoverFactory().get_stop_words()
    list_stopwords_nltk = stopwords.words('indonesian')
    custom_stopwords = ['padam', 'listrik']
    all_stopwords = set(list_stopwords_sastrawi + list_stopwords_nltk + custom_stopwords)

    tokens = [word for word in tokens if word not in all_stopwords]

    factory = StemmerFactory()
    stemmer = factory.create_stemmer()
    tokens = [stemmer.stem(word) for word in tokens]
    return " ".join(tokens)

# --- Fungsi Utama untuk Analisis Sentimen ---
def analyze_title_sentiment(text):
    print(f"\n--- SENTIMENT: Memulai analisis untuk teks: '{text}' ---")
    if model is None or vectorizer is None:
        print("--- SENTIMENT: Model tidak tersedia. Mengembalikan 'Netral'. ---")
        return "Netral"

    clean_text = preprocess_text(text)
    print(f"--- SENTIMENT: Teks setelah preprocessing: '{clean_text}' ---")

    if not clean_text.strip():
        print("--- SENTIMENT: Teks kosong setelah preprocessing. Mengembalikan 'Netral'. ---")
        return "Netral"

    try:
        text_vector = vectorizer.transform([clean_text])
        print("--- SENTIMENT: Teks berhasil di-transform oleh vectorizer. ---")
        
        prediction_label = model.predict(text_vector)[0]
        print(f"--- SENTIMENT: Model berhasil memprediksi label: {prediction_label} ---")

        if prediction_label == 0:
            return "Negatif"
        elif prediction_label == 1:
            return "Netral"
        elif prediction_label == 2:
            return "Positif"
        else:
            return "Netral" 

    except Exception as e:
        print(f"\n!!!!!! SENTIMENT ERROR: Gagal saat prediksi: {e} !!!!!!\n")
        return "Netral"