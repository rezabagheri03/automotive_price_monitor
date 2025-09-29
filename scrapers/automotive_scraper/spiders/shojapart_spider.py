"""
Spider for shojapart.com - Engine & Motor Parts
"""
from .base_spider import BaseAutomotiveSpider


class ShojapartSpider(BaseAutomotiveSpider):
    """Spider for scraping shojapart.com"""
    
    name = 'shojapart'
    site_name = 'shojapart.com'
    allowed_domains = ['shojapart.com']
    start_urls = ['https://shojapart.com']
    
    custom_settings = {
        **BaseAutomotiveSpider.custom_settings,
        'DOWNLOAD_DELAY': 2.4,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 5,
    }
    
    def _extract_category(self, response):
        return 'قطعات موتوری'
