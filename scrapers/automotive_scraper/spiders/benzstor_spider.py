"""
Spider for benzstor.com - Mercedes Parts
"""
from .base_spider import BaseAutomotiveSpider
from scrapy.http import Request
from urllib.parse import urljoin


class BenzstorSpider(BaseAutomotiveSpider):
    """Spider for scraping benzstor.com"""
    
    name = 'benzstor'
    site_name = 'benzstor.com'
    allowed_domains = ['benzstor.com']
    start_urls = ['https://benzstor.com']
    
    custom_settings = {
        **BaseAutomotiveSpider.custom_settings,
        'DOWNLOAD_DELAY': 2.0,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 6,
    }
    
    def _get_start_urls(self):
        """Get specific start URLs for benzstor.com"""
        base_url = 'https://benzstor.com'
        return [
            f"{base_url}/",
            f"{base_url}/shop/",
            f"{base_url}/mercedes-parts/",
            f"{base_url}/engine-parts/",
            f"{base_url}/accessories/",
        ]
