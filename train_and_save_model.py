# Nama File: train_and_save_model.py
# Lokasi: C:\HIKMAH MAHARANI\KERJA PRAKTIK\NLP PROJECT\Automation-Scrapper-With-Sentiment-Analysis\train_and_save_model.py

import pandas as pd
import re
import pickle # Pustaka untuk menyimpan/memuat objek Python
import nltk
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from imblearn.under_sampling import RandomUnderSampler
from sklearn.naive_bayes import MultinomialNB # Model yang Anda pilih
from sklearn.preprocessing import LabelEncoder # Untuk mengkodekan label sentimen
from scipy.sparse import hstack # Import untuk menggabungkan fitur


print("------ Script train_and_save_model.py dimulai ------")
print("--- Memulai script train_and_save_model.py ---")

# --- Bagian Download NLTK (Jalankan sekali jika belum terunduh) ---
try:
    nltk.data.find('tokenizers/punkt')
except nltk.downloader.DownloadError:
    nltk.download('punkt')
    print("NLTK 'punkt' diunduh.")

try:
    nltk.data.find('corpora/stopwords')
except nltk.downloader.DownloadError:
    nltk.download('stopwords')
    print("NLTK 'stopwords' diunduh.")

print("Pengecekan NLTK selesai.")


# === DEFINISI GLOBAL UNTUK FEATURE ENGINEERING (HARUS SAMA DI SENTIMENT.PY) ===
# Kata-kata yang kuat mengindikasikan konteks positif/netral meskipun ada kata negatif
# Pastikan ini kata dasar (stemmed) jika memungkinkan, atau tambahkan variasi
positive_context_words = ['mudah', 'aplikasi', 'akurat', 'bantu', 'solusi', 'inovasi', 'baik', 'normal', 'pulih', 'cek', 'sekitar']

# Kata-kata yang kuat mengindikasikan sentimen negatif (setelah preprocessing)
negative_core_words = ['padam', 'listrik', 'ganggu', 'keluh', 'rusak', 'mati', 'buruk', 'turun']
# ==============================================================================


# --- Fungsi Pra-pemrosesan Teks (Harus konsisten dengan yang akan digunakan di app) ---
def preprocess_text(text):
    if not isinstance(text, str):
        return ""
    text = text.lower() # Case Folding
    text = re.sub(r'[^a-zA-Z\s]', '', text) # Hapus karakter non-alfabet dan spasi
    tokens = word_tokenize(text) # Tokenisasi

    # Stopword Removal
    stop_factory = StopWordRemoverFactory()
    list_stopwords_sastrawi = stop_factory.get_stop_words()
    list_stopwords_nltk = stopwords.words('indonesian')
    
    # === PENTING: custom_stopwords ini TIDAK BOLEH mengandung kata yang ingin dinilai sentimennya ===
    # Contoh: 'padam', 'listrik', 'ganggu' TIDAK dimasukkan ke sini
    custom_stopwords = ['pln', 's2jb', 'uid', 'karena', 'akibat', 'sehingga', 'yakni', 'yaitu', 'terhadap', 'adalah', 'merupakan']
    all_stopwords = set(list_stopwords_sastrawi + list_stopwords_nltk + custom_stopwords)
    
    tokens = [word for word in tokens if word not in all_stopwords] # Pastikan all_stopwords di dalam scope

    # Stemming
    stem_factory = StemmerFactory()
    stemmer = stem_factory.create_stemmer()
    tokens = [stemmer.stem(word) for word in tokens] # FIX: 'word' for 'word'
    return " ".join(tokens)


# --- Proses Utama untuk Melatih dan Menyimpan Model ---
if __name__ == '__main__':
    print("Memulai proses pelatihan model dan pembuatan file .pkl...")

    # 1. Muat Dataset
    try:
        df = pd.read_csv('data/dataset_sentimen.csv')
        print(f"Dataset berhasil dimuat dari 'data/dataset_sentimen.csv'. Jumlah baris awal: {df.shape[0]}")
    except Exception as e:
        print(f"ERROR: Gagal memuat dataset dari 'data/dataset_sentimen.csv': {e}")
        print("Pastikan file 'dataset_sentimen.csv' ada di folder 'data' di root proyek Anda.")
        exit()

    # 2. Pembersihan dan Persiapan Data
    df = df.dropna().drop_duplicates()
    df = df.rename(columns={'Judul_informasi': 'judul', 'tonalitas': 'sentimen'})
    print(f"Jumlah baris setelah dropna dan drop_duplicates: {df.shape[0]}")

    # Encoding label sentimen
    le = LabelEncoder()
    df['sentimen_encoded'] = le.fit_transform(df['sentimen'])
    print(f"Kelas sentimen yang dienkode: {list(le.classes_)}")
    label_mapping_dict = dict(zip(le.transform(le.classes_), le.classes_))
    print(f"Mapping LabelEncoder: {label_mapping_dict}")

    # 3. Pra-pemrosesan Teks pada Kolom Judul
    df['judul_clean'] = df['judul'].apply(preprocess_text)
    print("Teks judul berhasil dipra-proses.")

    # === FEATURE ENGINEERING: Mendeteksi konteks netral/positif untuk kata-kata negatif ===
    # Buat fungsi untuk menghasilkan fitur biner (0 atau 1)
    def create_context_feature(clean_title_text):
        clean_title_tokens = clean_title_text.split()
        
        # Cek apakah judul mengandung kata negatif inti
        has_negative_trigger = any(word in clean_title_tokens for word in negative_core_words)
        
        # Cek apakah judul mengandung kata konteks positif/netral
        has_positive_context_trigger = any(word in clean_title_tokens for word in positive_context_words)
        
        # Fitur ini bernilai 1 jika ada kata negatif DAN kata konteks positif/netral
        # Ini menandakan kasus "negatif" yang sebenarnya netral karena konteksnya
        return 1 if has_negative_trigger and has_positive_context_trigger else 0

    df['has_positive_context_with_negative_trigger'] = df['judul_clean'].apply(create_context_feature)
    print(f"Distribusi fitur 'has_positive_context_with_negative_trigger':\n{df['has_positive_context_with_negative_trigger'].value_counts()}")
    # ====================================================================================

    # 4. Vectorisasi Teks (TF-IDF)
    vectorizer = TfidfVectorizer(ngram_range=(1, 2))
    X_text_features = vectorizer.fit_transform(df['judul_clean'])
    print(f"Data teks berhasil di-vectorize. Shape vektor teks: {X_text_features.shape}")

    # === MENGGABUNGKAN FITUR TEKS DENGAN FITUR BARU ===
    # Pastikan fitur baru adalah array 2D untuk hstack
    X = hstack([X_text_features, df[['has_positive_context_with_negative_trigger']].values])
    print(f"Shape vektor total setelah feature engineering: {X.shape}")
    # ===================================================

    # 5. Pembagian Data (Train-Test Split)
    X_train, X_test, y_train, y_test = train_test_split(
        X, df['sentimen_encoded'], test_size=0.15, random_state=42, stratify=df['sentimen_encoded']
    )
    print(f"Data dibagi: Train {X_train.shape[0]} samples, Test {X_test.shape[0]} samples.")

    # 6. Penanganan Ketidakseimbangan Data (Random Under-sampling)
    undersampler = RandomUnderSampler(random_state=42)
    X_resampled, y_resampled = undersampler.fit_resample(X_train, y_train)
    print(f"Distribusi sentimen setelah Under-sampling: \n{pd.Series(y_resampled).value_counts()}")

    # 7. Pelatihan Model (Multinomial Naive Bayes)
    model = MultinomialNB()
    model.fit(X_resampled, y_resampled)
    print("Model Naive Bayes berhasil dilatih.")

    # 8. Evaluasi Model
    from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
    y_pred = model.predict(X_test)
    print("\n--- Hasil Evaluasi Model ---")
    print(f"Akurasi: {accuracy_score(y_test, y_pred):.2f}")
    print("Classification Report:\n", classification_report(y_test, y_pred, target_names=le.classes_))
    print("Confusion Matrix:\n", confusion_matrix(y_test, y_pred))

    # 9. Menyimpan Model dan Vectorizer ke file .pkl
    try:
        with open('utils/sentiment_model.pkl', 'wb') as model_file:
            pickle.dump(model, model_file)

        with open('utils/tfidf_vectorizer.pkl', 'wb') as vec_file:
            pickle.dump(vectorizer, vec_file)

        print("\n====================================================================")
        print("SUCCESS: File sentiment_model.pkl dan tfidf_vectorizer.pkl berhasil dibuat.")
        print("Keduanya tersimpan di folder 'utils/' di root proyek Anda.")
        print("Anda sekarang bisa menjalankan aplikasi Flask Anda.")
        print("====================================================================")

    except Exception as e:
        print(f"\nERROR KRITIS: Gagal menyimpan model atau vectorizer: {e}")
        print("Pastikan folder 'utils' ada di direktori yang sama dengan script ini dan Anda memiliki izin tulis.")