"""
Spider for auto-nik.com - ABS, ECU & Wiring parts
"""
from .base_spider import BaseAutomotiveSpider
from scrapy.http import Request
from urllib.parse import urljoin


class AutonikSpider(BaseAutomotiveSpider):
    """Spider for scraping auto-nik.com"""
    
    name = 'autonik'
    site_name = 'auto-nik.com'
    allowed_domains = ['auto-nik.com']
    start_urls = ['https://auto-nik.com']
    
    custom_settings = {
        **BaseAutomotiveSpider.custom_settings,
        'DOWNLOAD_DELAY': 2.0,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 5,
    }
    
    def _get_start_urls(self):
        """Get specific start URLs for auto-nik.com"""
        base_url = 'https://auto-nik.com'
        return [
            f"{base_url}/",
            f"{base_url}/product-category/abs/",
            f"{base_url}/product-category/ecu/",
            f"{base_url}/product-category/wiring/",
            f"{base_url}/product-category/airbag/",
            f"{base_url}/product-category/sensors/",
        ]
    
    def parse(self, response):
        """Parse category and product listing pages"""
        # Extract product links
        product_links = response.css('a[href*="/product/"]::attr(href)').getall()
        
        for link in product_links:
            yield Request(
                url=urljoin(response.url, link),
                callback=self.parse_product,
                meta={'session_id': self.session_id}
            )
        
        # Follow category links
        category_links = response.css('.product-category a::attr(href)').getall()
        for link in category_links:
            if '/product-category/' in link:
                yield Request(
                    url=urljoin(response.url, link),
                    callback=self.parse,
                    meta={'session_id': self.session_id}
                )
        
        # Follow pagination
        next_page = response.css('.next.page-numbers::attr(href)').get()
        if next_page:
            yield Request(
                url=urljoin(response.url, next_page),
                callback=self.parse,
                meta={'session_id': self.session_id}
            )
    
    def _extract_name(self, response):
        """Extract product name for auto-nik.com"""
        name = response.css('h1.entry-title::text').get()
        if not name:
            name = response.css('.product-title::text').get()
        return name.strip() if name else None
    
    def _extract_price(self, response):
        """Extract price for auto-nik.com"""
        # Try different price selectors
        price_selectors = [
            '.woocommerce-Price-amount bdi::text',
            '.price .amount::text',
            '.price-value::text'
        ]
        
        for selector in price_selectors:
            price_text = response.css(selector).get()
            if price_text:
                import re
                price_cleaned = re.sub(r'[^\d.,]', '', price_text)
                try:
                    return float(price_cleaned.replace(',', ''))
                except:
                    continue
        
        return None
    
    def _extract_category(self, response):
        """Extract category for auto-nik.com"""
        # Try breadcrumbs
        breadcrumbs = response.css('.breadcrumb a::text').getall()
        if breadcrumbs and len(breadcrumbs) > 1:
            category = breadcrumbs[-2].strip()
            
            # Map to Persian categories
            category_map = {
                'abs': 'سیستم ترمز',
                'ecu': 'لوازم الکترونیک و سنسورها',
                'wiring': 'لوازم الکترونیک و سنسورها',
                'airbag': 'قطعات بدنه و داخل کابین',
                'sensors': 'لوازم الکترونیک و سنسورها',
            }
            
            for key, value in category_map.items():
                if key.lower() in category.lower():
                    return value
            
            return category
        
        return 'لوازم الکترونیک و سنسورها'
    
    def _extract_availability(self, response):
        """Extract availability for auto-nik.com"""
        stock_status = response.css('.stock::text').get()
        if stock_status:
            if 'موجود' in stock_status or 'in stock' in stock_status.lower():
                return 'موجود'
            elif 'ناموجود' in stock_status or 'out of stock' in stock_status.lower():
                return 'ناموجود'
        
        # Check if add to cart button exists
        add_to_cart = response.css('.single_add_to_cart_button').get()
        return 'موجود' if add_to_cart else 'ناموجود'
