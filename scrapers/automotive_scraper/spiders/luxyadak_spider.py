"""
Spider for luxyadak.com - Luxury Car Parts
"""
from .base_spider import BaseAutomotiveSpider


class LuxyadakSpider(BaseAutomotiveSpider):
    """Spider for scraping luxyadak.com"""
    
    name = 'luxyadak'
    site_name = 'luxyadak.com'
    allowed_domains = ['luxyadak.com']
    start_urls = ['https://luxyadak.com']
    
    custom_settings = {
        **BaseAutomotiveSpider.custom_settings,
        'DOWNLOAD_DELAY': 1.9,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 6,
    }
