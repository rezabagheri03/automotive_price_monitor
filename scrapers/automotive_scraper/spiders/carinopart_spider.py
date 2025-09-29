"""
Spider for carinopart.com - Auto Components
"""
from .base_spider import BaseAutomotiveSpider
from scrapy.http import Request
from urllib.parse import urljoin


class CarinopartSpider(BaseAutomotiveSpider):
    """Spider for scraping carinopart.com"""
    
    name = 'carinopart'
    site_name = 'carinopart.com'
    allowed_domains = ['carinopart.com']
    start_urls = ['https://carinopart.com']
    
    custom_settings = {
        **BaseAutomotiveSpider.custom_settings,
        'DOWNLOAD_DELAY': 2.2,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 4,
    }
    
    def _get_start_urls(self):
        base_url = 'https://carinopart.com'
        return [
            f"{base_url}/",
            f"{base_url}/auto-components/",
            f"{base_url}/engine-parts/",
            f"{base_url}/electrical-parts/",
        ]
    
    def _extract_category(self, response):
        return 'لوازم جانبی خودرو'
