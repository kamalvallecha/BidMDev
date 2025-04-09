import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database configuration
    POSTGRES_DB = os.getenv('DB_NAME', 'BidM')
    POSTGRES_USER = os.getenv('DB_USER', 'postgres')
    POSTGRES_PASSWORD = os.getenv('DB_PASSWORD', 'admin123')
    POSTGRES_HOST = os.getenv('DB_HOST', 'localhost')
    POSTGRES_PORT = os.getenv('DB_PORT', '5432')

    # JWT configuration
    SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-jwt-secret-key')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-jwt-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)

    # Other configuration
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    CORS_HEADERS = 'Content-Type' 