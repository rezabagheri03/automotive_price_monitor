"""
Spider for parsianlent.com - Brake Components
"""
from .base_spider import BaseAutomotiveSpider


class ParsianlentSpider(BaseAutomotiveSpider):
    """Spider for scraping parsianlent.com"""
    
    name = 'parsianlent'
    site_name = 'parsianlent.com'
    allowed_domains = ['parsianlent.com']
    start_urls = ['https://parsianlent.com']
    
    custom_settings = {
        **BaseAutomotiveSpider.custom_settings,
        'DOWNLOAD_DELAY': 2.1,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 5,
    }
    
    def _extract_category(self, response):
        return 'سیستم ترمز'
