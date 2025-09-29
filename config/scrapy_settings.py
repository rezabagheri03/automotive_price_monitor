"""
Scrapy configuration settings for automotive price scraping
"""
import os
from .settings import Config

config = Config()

# Scrapy settings for automotive_scraper project
SCRAPY_SETTINGS = {
    'BOT_NAME': 'automotive_scraper',
    
    'SPIDER_MODULES': ['scrapers.automotive_scraper.spiders'],
    'NEWSPIDER_MODULE': 'scrapers.automotive_scraper.spiders',
    
    # Obey robots.txt rules (set to False if needed)
    'ROBOTSTXT_OBEY': True,
    
    # Configure maximum concurrent requests
    'CONCURRENT_REQUESTS': config.CONCURRENT_REQUESTS,
    'CONCURRENT_REQUESTS_PER_DOMAIN': min(config.CONCURRENT_REQUESTS // 4, 16),
    
    # Configure delays
    'DOWNLOAD_DELAY': config.DOWNLOAD_DELAY,
    'RANDOMIZE_DOWNLOAD_DELAY': config.RANDOMIZE_DOWNLOAD_DELAY,
    
    # AutoThrottle settings
    'AUTOTHROTTLE_ENABLED': True,
    'AUTOTHROTTLE_START_DELAY': 1,
    'AUTOTHROTTLE_MAX_DELAY': 10,
    'AUTOTHROTTLE_TARGET_CONCURRENCY': 2.0,
    'AUTOTHROTTLE_DEBUG': False,
    
    # Configure pipelines
    'ITEM_PIPELINES': {
        'scrapers.automotive_scraper.pipelines.ValidationPipeline': 300,
        'scrapers.automotive_scraper.pipelines.DatabasePipeline': 400,
        'scrapers.automotive_scraper.pipelines.DuplicatesPipeline': 500,
    },
    
    # Configure middlewares
    'DOWNLOADER_MIDDLEWARES': {
        'scrapers.automotive_scraper.middlewares.ProxyMiddleware': 100,
        'scrapers.automotive_scraper.middlewares.UserAgentMiddleware': 200,
        'scrapers.automotive_scraper.middlewares.RetryMiddleware': 300,
        'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': None,
        'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    },
    
    # Configure User-Agent
    'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    
    # Configure request headers
    'DEFAULT_REQUEST_HEADERS': {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'fa-IR,fa;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    },
    
    # Configure cookies
    'COOKIES_ENABLED': True,
    'COOKIES_DEBUG': False,
    
    # Configure retries
    'RETRY_ENABLED': True,
    'RETRY_TIMES': 3,
    'RETRY_HTTP_CODES': [500, 502, 503, 504, 408, 429],
    
    # Configure redirects
    'REDIRECT_ENABLED': True,
    'REDIRECT_MAX_TIMES': 5,
    
    # Configure timeouts
    'DOWNLOAD_TIMEOUT': 30,
    
    # Configure logging
    'LOG_LEVEL': config.LOG_LEVEL,
    'LOG_FILE': os.path.join(config.LOGS_DIR, 'scrapy.log'),
    
    # Configure cache (optional)
    'HTTPCACHE_ENABLED': False,
    'HTTPCACHE_EXPIRATION_SECS': 3600,
    'HTTPCACHE_DIR': 'httpcache',
    
    # Configure feed exports
    'FEEDS': {
        os.path.join(config.DATA_DIR, 'scraped_data.json'): {
            'format': 'json',
            'encoding': 'utf8',
            'store_empty': False,
            'overwrite': True,
        },
    },
    
    # Configure stats collection
    'STATS_CLASS': 'scrapy.statscollectors.MemoryStatsCollector',
    
    # Disable telnet console (security)
    'TELNETCONSOLE_ENABLED': False,
    
    # Configure DNS
    'DNSCACHE_ENABLED': True,
    'DNSCACHE_SIZE': 10000,
    'DNS_TIMEOUT': 60,
    
    # Configure extensions
    'EXTENSIONS': {
        'scrapy.extensions.telnet.TelnetConsole': None,
        'scrapy.extensions.memusage.MemoryUsage': 100,
        'scrapy.extensions.closespider.CloseSpider': 200,
    },
    
    # Memory usage settings
    'MEMUSAGE_ENABLED': True,
    'MEMUSAGE_LIMIT_MB': 2048,
    'MEMUSAGE_WARNING_MB': 1024,
    
    # Close spider settings
    'CLOSESPIDER_TIMEOUT': 3600,  # 1 hour timeout
    'CLOSESPIDER_ITEMCOUNT': 50000,  # Close after 50k items
    'CLOSESPIDER_PAGECOUNT': 100000,  # Close after 100k pages
    'CLOSESPIDER_ERRORCOUNT': 100,  # Close after 100 errors
    
    # Custom settings for Iranian sites
    'IRANIAN_SITES_CONFIG': {
        'auto-nik.com': {
            'delay': 2.0,
            'concurrent': 5,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        },
        'bmwstor.com': {
            'delay': 1.5,
            'concurrent': 8,
            'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        },
        'benzstor.com': {
            'delay': 2.0,
            'concurrent': 6,
            'user_agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        },
        'mryadaki.com': {
            'delay': 1.8,
            'concurrent': 10,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        },
        'carinopart.com': {
            'delay': 2.2,
            'concurrent': 4,
            'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15'
        },
        'japanstor.com': {
            'delay': 1.6,
            'concurrent': 7,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101'
        },
        'shojapart.com': {
            'delay': 2.4,
            'concurrent': 5,
            'user_agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:91.0) Gecko/20100101'
        },
        'luxyadak.com': {
            'delay': 1.9,
            'concurrent': 6,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        },
        'parsianlent.com': {
            'delay': 2.1,
            'concurrent': 5,
            'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        },
        'iranrenu.com': {
            'delay': 1.7,
            'concurrent': 8,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        },
        'automoby.ir': {
            'delay': 2.3,
            'concurrent': 4,
            'user_agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        },
        'oil-city.ir': {
            'delay': 1.4,
            'concurrent': 9,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    }
}
