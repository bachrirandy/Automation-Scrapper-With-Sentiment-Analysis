# Nama File: train_and_save_model.py
# Lokasi: C:\HIKMAH MAHARANI\KERJA PRAKTIK\NLP PROJECT\Automation-Scrapper-With-Sentiment-Analysis\train_and_save_model.py
print("------ Script train_and_save_model.py dimulai ------")
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

print("--- Memulai script train_and_save_model.py ---")

# --- Bagian Download NLTK (Jalankan sekali jika belum terunduh) ---
# Tambahkan pengecekan agar tidak mengunduh berulang kali
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


# --- Fungsi Pra-pemrosesan Teks (Harus konsisten dengan yang akan digunakan di app) ---
def preprocess_text(text):
    if not isinstance(text, str):
        return "" # Pastikan input adalah string
    text = text.lower() # Case Folding
    text = re.sub(r'[^a-zA-Z\s]', '', text) # Hapus karakter non-alfabet dan spasi
    tokens = word_tokenize(text) # Tokenisasi

    # Stopword Removal
    stop_factory = StopWordRemoverFactory()
    list_stopwords_sastrawi = stop_factory.get_stop_words()
    list_stopwords_nltk = stopwords.words('indonesian')
    # === PENTING: Tambahkan stopword kustom di sini untuk mengatasi "padam" dll. ===
    custom_stopwords = ['padam', 'listrik', 'pln', 's2jb', 'uid', 'ganggu', 'layanan', 'warga', 'karena', 'akibat']
    all_stopwords = set(list_stopwords_sastrawi + list_stopwords_nltk + custom_stopwords)
    tokens = [word for word in tokens if word not in all_stopwords]

    # Stemming
    stem_factory = StemmerFactory()
    stemmer = stem_factory.create_stemmer()
    tokens = [stemmer.stem(word) for word in tokens]
    return " ".join(tokens) # Gabungkan kembali token menjadi string

# --- Proses Utama untuk Melatih dan Menyimpan Model ---
if __name__ == '__main__':
    print("Memulai proses pelatihan model dan pembuatan file .pkl...")

    # 1. Muat Dataset
    try:
        # === PENTING: Ganti dengan path file lokal Anda yang sudah diunduh ===
        df = pd.read_csv('data/dataset_sentimen.csv')
        print(f"Dataset berhasil dimuat dari 'data/dataset_sentimen.csv'. Jumlah baris awal: {df.shape[0]}")
    except Exception as e:
        print(f"ERROR: Gagal memuat dataset dari 'data/dataset_sentimen.csv': {e}")
        print("Pastikan file 'dataset_sentimen.csv' ada di folder 'data' di root proyek Anda.")
        exit() # Hentikan eksekusi jika dataset gagal dimuat

    # 2. Pembersihan dan Persiapan Data
    df = df.dropna().drop_duplicates()
    df = df.rename(columns={'Judul_informasi': 'judul', 'tonalitas': 'sentimen'})
    print(f"Jumlah baris setelah dropna dan drop_duplicates: {df.shape[0]}")

    # Encoding label sentimen
    le = LabelEncoder()
    # Fit LabelEncoder pada semua kelas sentimen yang mungkin
    # Urutan default LabelEncoder adalah alfabetis: 'negatif', 'netral', 'positif'
    df['sentimen_encoded'] = le.fit_transform(df['sentimen'])

    # === PENTING: Perhatikan mapping yang dihasilkan oleh LabelEncoder ===
    # Ini sangat penting agar Anda tahu label mana yang berkorespondensi dengan angka berapa
    # Contoh: {0: 'negatif', 1: 'netral', 2: 'positif'}
    # Anda akan menggunakan ini di utils/sentiment.py
    print(f"Kelas sentimen yang dienkode: {list(le.classes_)}")
    label_mapping_dict = dict(zip(le.transform(le.classes_), le.classes_))
    print(f"Mapping LabelEncoder: {label_mapping_dict}")

    # 3. Pra-pemrosesan Teks pada Kolom Judul
    df['judul_clean'] = df['judul'].apply(preprocess_text)
    print("Teks judul berhasil dipra-proses.")

    # 4. Vectorisasi Teks (TF-IDF)
    # n-gram_range=(1,2) akan menghasilkan unigram (kata tunggal) dan bigram (dua kata berurutan)
    # Ini membantu menangkap konteks kata
    vectorizer = TfidfVectorizer(ngram_range=(1, 2))
    X_vectorized = vectorizer.fit_transform(df['judul_clean'])
    print(f"Data teks berhasil di-vectorize. Shape vektor: {X_vectorized.shape}")

    # 5. Pembagian Data (Train-Test Split)
    X_train, X_test, y_train, y_test = train_test_split(
        X_vectorized, df['sentimen_encoded'], test_size=0.15, random_state=42, stratify=df['sentimen_encoded']
    )
    print(f"Data dibagi: Train {X_train.shape[0]} samples, Test {X_test.shape[0]} samples.")

    # 6. Penanganan Ketidakseimbangan Data (Random Under-sampling)
    undersampler = RandomUnderSampler(random_state=42)
    X_resampled, y_resampled = undersampler.fit_resample(X_train, y_train)
    print(f"Distribusi sentimen setelah Under-sampling: \n{pd.Series(y_resampled).value_counts()}")

    # 7. Pelatihan Model (Multinomial Naive Bayes adalah pilihan yang baik untuk teks)
    model = MultinomialNB() # Atau SVC(kernel='linear') jika ingin mencoba SVC
    model.fit(X_resampled, y_resampled)
    print("Model Naive Bayes berhasil dilatih.")

    # 8. Evaluasi Model (Opsional, untuk verifikasi kinerja)
    from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
    y_pred = model.predict(X_test)
    print("\n--- Hasil Evaluasi Model ---")
    print(f"Akurasi: {accuracy_score(y_test, y_pred):.2f}")
    # Gunakan `le.classes_` untuk nama target agar classification report terbaca
    print("Classification Report:\n", classification_report(y_test, y_pred, target_names=le.classes_))
    print("Confusion Matrix:\n", confusion_matrix(y_test, y_pred))

    # 9. Menyimpan Model dan Vectorizer ke file .pkl
    # === PENTING: Lokasi penyimpanan HARUS di folder 'utils/' ===
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