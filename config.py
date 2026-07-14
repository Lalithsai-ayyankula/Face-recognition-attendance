# config.py
import os
from datetime import timedelta

class Config:
    """Application configuration settings."""
    # Use environment variables for sensitive settings with fallbacks
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production-12345678')
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    SESSION_TYPE = 'filesystem'
    SESSION_COOKIE_SECURE = False  # Set to False for development (http)
    SESSION_COOKIE_HTTPONLY = False  # Changed to False for cross-IP
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_NAME = 'session'
    
    # CSRF Configuration - Disable for development
    WTF_CSRF_ENABLED = False  # Disable CSRF for now
    WTF_CSRF_TIME_LIMIT = None
    WTF_CSRF_CHECK_DEFAULT = False
    
    # MongoDB configuration
    MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
    MONGO_DB = os.environ.get('MONGO_DB', 'attendance_system')
    
    # Face recognition settings
    FACE_RECOGNITION_TOLERANCE = float(os.environ.get('FACE_RECOGNITION_TOLERANCE', '0.6'))
    FACE_RECOGNITION_MODEL = os.environ.get('FACE_RECOGNITION_MODEL', 'hog')  # 'hog' or 'cnn'
    
    # File storage
    DATA_DIR = os.environ.get('DATA_DIR', 'data')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')