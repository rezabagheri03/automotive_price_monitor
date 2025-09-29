"""
Spider for japanstor.com - Japanese Car Parts
"""
from .base_spider import BaseAutomotiveSpider


class JapanstorSpider(BaseAutomotiveSpider):
    """Spider for scraping japanstor.com"""
    
    name = 'japanstor'
    site_name = 'japanstor.com'
    allowed_domains = ['japanstor.com']
    start_urls = ['https://japanstor.com']
    
    custom_settings = {
        **BaseAutomotiveSpider.custom_settings,
        'DOWNLOAD_DELAY': 1.6,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 7,
    }
    
    def _get_start_urls(self):
        base_url = 'https://japanstor.com'
        return [
            f"{base_url}/",
            f"{base_url}/honda-parts/",
            f"{base_url}/toyota-parts/", 
            f"{base_url}/nissan-parts/",
        ]
