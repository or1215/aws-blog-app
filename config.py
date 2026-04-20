# config.py
import os

class Config:
    DB_CONFIG = {
        'host': os.environ.get('DB_HOST'),
        'user': os.environ.get('DB_USER'),
        'password': os.environ.get('DB_PASSWORD'),
        'database': os.environ.get('DB_NAME'),
        'charset': 'utf8mb4'
    }
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-key-for-dev')