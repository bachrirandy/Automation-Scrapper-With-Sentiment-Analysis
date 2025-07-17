# pln-news-monitor/config.py
import os

class Config:
    # Baris ini akan mencari SECRET_KEY dari .env
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'kunci-default-jika-tidak-ditemukan'
    DATABASE_NAME = 'database.db'