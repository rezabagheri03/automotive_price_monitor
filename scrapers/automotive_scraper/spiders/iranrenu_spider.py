"""
Spider for iranrenu.com - Renault Parts
"""
from .base_spider import BaseAutomotiveSpider


class IranrenuSpider(BaseAutomotiveSpider):
    """Spider for scraping iranrenu.com"""
    
    name = 'iranrenu'
    site_name = 'iranrenu.com'
    allowed_domains = ['iranrenu.com']
    start_urls = ['https://iranrenu.com']
    
    custom_settings = {
        **BaseAutomotiveSpider.custom_settings,
        'DOWNLOAD_DELAY': 1.7,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 8,
    }
