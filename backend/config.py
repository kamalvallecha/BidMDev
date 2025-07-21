import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Database configuration - Use Replit DB
    USE_REPLIT_DB = True
    DATABASE_URL = os.getenv('DATABASE_URL', 'replit://default')

    # JWT configuration
    SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-jwt-secret-key')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-jwt-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)

    # Other configuration
    DEBUG = True
    CORS_HEADERS = 'Content-Type'
