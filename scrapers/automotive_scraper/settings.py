"""
Scrapy settings for automotive_scraper project
"""
import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, project_root)

from config.scrapy_settings import SCRAPY_SETTINGS

# Import all settings from config
locals().update(SCRAPY_SETTINGS)

# Additional scrapy-specific settings
BOT_NAME = 'automotive_scraper'

SPIDER_MODULES = ['scrapers.automotive_scraper.spiders']
NEWSPIDER_MODULE = 'scrapers.automotive_scraper.spiders'

# Enable and configure the AutoThrottle extension
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 60
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching
HTTPCACHE_ENABLED = False
HTTPCACHE_EXPIRATION_SECS = 0
HTTPCACHE_DIR = 'httpcache'
HTTPCACHE_IGNORE_HTTP_CODES = []
HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'
