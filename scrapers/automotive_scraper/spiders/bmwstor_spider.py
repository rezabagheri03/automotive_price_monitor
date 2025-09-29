"""
Spider for bmwstor.com - BMW Parts & Accessories
"""
from .base_spider import BaseAutomotiveSpider
from scrapy.http import Request
from urllib.parse import urljoin


class BmwstorSpider(BaseAutomotiveSpider):
    """Spider for scraping bmwstor.com"""
    
    name = 'bmwstor'
    site_name = 'bmwstor.com'
    allowed_domains = ['bmwstor.com']
    start_urls = ['https://bmwstor.com']
    
    custom_settings = {
        **BaseAutomotiveSpider.custom_settings,
        'DOWNLOAD_DELAY': 1.5,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 8,
    }
    
    def _get_start_urls(self):
        """Get specific start URLs for bmwstor.com"""
        base_url = 'https://bmwstor.com'
        return [
            f"{base_url}/",
            f"{base_url}/shop/",
            f"{base_url}/product-category/bmw-parts/",
            f"{base_url}/product-category/accessories/",
            f"{base_url}/product-category/engine-parts/",
            f"{base_url}/product-category/body-parts/",
        ]
    
    def parse(self, response):
        """Parse BMW parts pages"""
        # Extract product links
        product_links = response.css('a.woocommerce-LoopProduct-link::attr(href)').getall()
        
        for link in product_links:
            yield Request(
                url=link,
                callback=self.parse_product,
                meta={'session_id': self.session_id}
            )
        
        # Follow pagination
        next_page = response.css('.woocommerce-pagination .next::attr(href)').get()
        if next_page:
            yield Request(
                url=next_page,
                callback=self.parse,
                meta={'session_id': self.session_id}
            )
    
    def _extract_name(self, response):
        """Extract product name for bmwstor.com"""
        name = response.css('h1.product_title::text').get()
        return name.strip() if name else None
    
    def _extract_price(self, response):
        """Extract price for bmwstor.com"""
        price_text = response.css('.woocommerce-Price-amount bdi::text').get()
        if price_text:
            import re
            price_cleaned = re.sub(r'[^\d.,]', '', price_text)
            try:
                return float(price_cleaned.replace(',', ''))
            except:
                pass
        return None
    
    def _extract_category(self, response):
        """Extract category for bmwstor.com"""
        # Try product category
        category = response.css('.product_meta .posted_in a::text').get()
        if category:
            category = category.strip()
            
            # Map BMW categories to Persian
            category_map = {
                'engine': 'قطعات موتوری',
                'body': 'قطعات بدنه و داخل کابین',
                'accessories': 'لوازم جانبی خودرو',
                'electrical': 'لوازم الکترونیک و سنسورها',
                'brake': 'سیستم ترمز',
                'suspension': 'جلوبندی و تعلیق و سیستم فرمان',
            }
            
            for key, value in category_map.items():
                if key.lower() in category.lower():
                    return value
            
            return category
        
        return 'لوازم جانبی خودرو'
