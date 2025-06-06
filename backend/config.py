import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database configuration
    DATABASE_URL = "postgresql://postgres:root123@localhost:5432/BidM"

    # JWT configuration
    SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-jwt-secret-key')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-jwt-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)

    # Other configuration
    DEBUG = True
    CORS_HEADERS = 'Content-Type'
