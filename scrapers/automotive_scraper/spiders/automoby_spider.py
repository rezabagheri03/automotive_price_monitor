"""
Spider for automoby.ir - Auto Marketplace
"""
from .base_spider import BaseAutomotiveSpider


class AutomobySpider(BaseAutomotiveSpider):
    """Spider for scraping automoby.ir"""
    
    name = 'automoby'
    site_name = 'automoby.ir'
    allowed_domains = ['automoby.ir']
    start_urls = ['https://automoby.ir']
    
    custom_settings = {
        **BaseAutomotiveSpider.custom_settings,
        'DOWNLOAD_DELAY': 2.3,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 4,
    }
