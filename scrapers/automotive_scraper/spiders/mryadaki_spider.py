"""
Spider for mryadaki.com - General Auto Parts
"""
from .base_spider import BaseAutomotiveSpider
from scrapy.http import Request
from urllib.parse import urljoin


class MryadakiSpider(BaseAutomotiveSpider):
    """Spider for scraping mryadaki.com"""
    
    name = 'mryadaki'
    site_name = 'mryadaki.com'
    allowed_domains = ['mryadaki.com']
    start_urls = ['https://mryadaki.com']
    
    custom_settings = {
        **BaseAutomotiveSpider.custom_settings,
        'DOWNLOAD_DELAY': 1.8,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 10,
    }
    
    def _get_start_urls(self):
        """Get specific start URLs for mryadaki.com"""
        base_url = 'https://mryadaki.com'
        return [
            f"{base_url}/",
            f"{base_url}/shop/",
            f"{base_url}/category/engine-parts/",
            f"{base_url}/category/transmission/",
            f"{base_url}/category/electrical/",
            f"{base_url}/category/filters/",
        ]
    
    def _extract_category(self, response):
        """Extract category for mryadaki.com"""
        breadcrumbs = response.css('.breadcrumb a::text').getall()
        if breadcrumbs and len(breadcrumbs) > 1:
            category = breadcrumbs[-2].strip()
            
            category_map = {
                'engine': 'قطعات موتوری',
                'transmission': 'گیربکس و انتقال قدرت',
                'electrical': 'لوازم الکترونیک و سنسورها',
                'filters': 'فیلتر و صافی',
                'brake': 'سیستم ترمز',
                'suspension': 'جلوبندی و تعلیق و سیستم فرمان',
            }
            
            for key, value in category_map.items():
                if key.lower() in category.lower():
                    return value
            
            return category
        
        return 'لوازم جانبی خودرو'
