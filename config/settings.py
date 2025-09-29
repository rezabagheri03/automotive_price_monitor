"""
Application configuration settings
"""
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration class"""
    
    # Flask Settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    
    # Database Settings
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    DB_NAME = os.getenv('DB_NAME', 'automotive_prices')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    
    # SQLAlchemy Configuration
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True
    }
    
    # WooCommerce Settings
    WOOCOMMERCE_URL = os.getenv('WOOCOMMERCE_URL', 'https://www.lavazembazaar.com')
    WOOCOMMERCE_CONSUMER_KEY = os.getenv('WOOCOMMERCE_CONSUMER_KEY', '')
    WOOCOMMERCE_CONSUMER_SECRET = os.getenv('WOOCOMMERCE_CONSUMER_SECRET', '')
    WOOCOMMERCE_API_VERSION = 'wc/v3'
    
    # Email Configuration
    EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
    EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
    EMAIL_USER = os.getenv('EMAIL_USER', '')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '')
    EMAIL_FROM = os.getenv('EMAIL_FROM', 'noreply@lavazembazaar.com')
    EMAIL_TO = os.getenv('EMAIL_TO', 'admin@lavazembazaar.com')
    
    # Redis Configuration
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_DB = int(os.getenv('REDIS_DB', 0))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)
    REDIS_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}" if REDIS_PASSWORD else f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
    
    # Scraping Configuration
    CONCURRENT_REQUESTS = int(os.getenv('CONCURRENT_REQUESTS', 50))
    DOWNLOAD_DELAY = float(os.getenv('DOWNLOAD_DELAY', 2.0))
    RANDOMIZE_DOWNLOAD_DELAY = float(os.getenv('RANDOMIZE_DOWNLOAD_DELAY', 0.5))
    USER_AGENT_ROTATION = os.getenv('USER_AGENT_ROTATION', 'true').lower() == 'true'
    
    # Proxy Configuration
    PROXY_ENABLED = os.getenv('PROXY_ENABLED', 'false').lower() == 'true'
    PROXY_LIST = os.getenv('PROXY_LIST', '').split(',') if os.getenv('PROXY_LIST') else []
    PROXY_AUTH = os.getenv('PROXY_AUTH', '')
    
    # Monitoring & Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    SENTRY_DSN = os.getenv('SENTRY_DSN', '')
    ENABLE_MONITORING = os.getenv('ENABLE_MONITORING', 'true').lower() == 'true'
    
    # File Paths
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    LOGS_DIR = os.path.join(BASE_DIR, 'logs')
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    BACKUP_PATH = os.getenv('BACKUP_PATH', '/var/backups/automotive_prices')
    
    # Security Settings
    BCRYPT_LOG_ROUNDS = int(os.getenv('BCRYPT_LOG_ROUNDS', 12))
    SESSION_PERMANENT = os.getenv('SESSION_PERMANENT', 'false').lower() == 'true'
    PERMANENT_SESSION_LIFETIME = timedelta(seconds=int(os.getenv('PERMANENT_SESSION_LIFETIME', 3600)))
    
    # Create directories if they don't exist
    @classmethod
    def init_app(cls, app):
        os.makedirs(cls.LOGS_DIR, exist_ok=True)
        os.makedirs(cls.DATA_DIR, exist_ok=True)
        os.makedirs(cls.BACKUP_PATH, exist_ok=True)


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    CONCURRENT_REQUESTS = 10
    DOWNLOAD_DELAY = 3.0


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    # Override with production-specific settings
    CONCURRENT_REQUESTS = int(os.getenv('CONCURRENT_REQUESTS', 100))
    DOWNLOAD_DELAY = float(os.getenv('DOWNLOAD_DELAY', 1.5))


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    DB_NAME = 'automotive_prices_test'
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{Config.DB_USER}:{Config.DB_PASSWORD}@{Config.DB_HOST}:{Config.DB_PORT}/automotive_prices_test"
    CONCURRENT_REQUESTS = 5
    DOWNLOAD_DELAY = 0.5


# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
