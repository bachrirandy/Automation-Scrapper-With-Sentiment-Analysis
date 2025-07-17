# pln-news-monitor/utils/sentiment.py

from pysentimiento import create_analyzer

# Inisialisasi analyzer. Model akan diunduh otomatis saat pertama kali dijalankan.
try:
    sentiment_analyzer = create_analyzer(task="sentiment", lang="id")
except Exception as e:
    print(f"Gagal memuat model sentimen: {e}")
    sentiment_analyzer = None

def analyze_title_sentiment(title):
    """
    Menganalisis sentimen teks dan mengembalikan tonalitas.
    """
    if not sentiment_analyzer or not title:
        return "Netral"
        
    try:
        result = sentiment_analyzer.predict(title)
        output = result.output
        if output == 'POS':
            return 'Positif'
        elif output == 'NEG':
            return 'Negatif'
        else: # NEU
            return 'Netral'
            
    except Exception as e:
        print(f"Error menganalisis sentimen: {e}")
        return "Netral"