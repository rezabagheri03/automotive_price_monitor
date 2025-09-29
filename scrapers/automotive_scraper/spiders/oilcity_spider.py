"""
Spider for oil-city.ir - Oils & Fluids
"""
from .base_spider import BaseAutomotiveSpider


class OilcitySpider(BaseAutomotiveSpider):
    """Spider for scraping oil-city.ir"""
    
    name = 'oilcity'
    site_name = 'oil-city.ir'
    allowed_domains = ['oil-city.ir', 'www.oil-city.ir']
    start_urls = ['https://www.oil-city.ir']
    
    custom_settings = {
        **BaseAutomotiveSpider.custom_settings,
        'DOWNLOAD_DELAY': 1.4,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 9,
    }
    
    def _extract_category(self, response):
        return 'روغن و مایعات'
