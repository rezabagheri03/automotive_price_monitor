"""
Base spider class for automotive parts scraping
"""
import scrapy
import json
import uuid
from datetime import datetime
from urllib.parse import urljoin, urlparse
from scrapy.http import Request
from ..items import AutomotiveProductItem
from database.models import SiteConfig
from config.database import db_manager
from utils.logger import setup_logger

logger = setup_logger(__name__)


class BaseAutomotiveSpider(scrapy.Spider):
    """Base spider for automotive parts websites"""
    
    name = 'base_automotive'
    allowed_domains = []
    start_urls = []
    
    custom_settings = {
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 2.0,
        'RANDOMIZE_DOWNLOAD_DELAY': 0.5,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 5,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 1,
        'AUTOTHROTTLE_MAX_DELAY': 10,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 2.0,
    }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.site_config = None
        self.session_id = str(uuid.uuid4())
        self.scraped_count = 0
        self.error_count = 0
        self.start_time = datetime.utcnow()
        
        # Load site configuration
        self._load_site_config()
        
        # Setup category mappings
        self._load_category_mappings()
    
    def _load_site_config(self):
        """Load site configuration from database"""
        try:
            with db_manager.get_session() as session:
                self.site_config = session.query(SiteConfig).filter_by(
                    site_name=self.site_name
                ).first()
                
            if self.site_config:
                # Update spider settings based on config
                self.custom_settings.update({
                    'DOWNLOAD_DELAY': float(self.site_config.request_delay or 2.0),
                    'CONCURRENT_REQUESTS_PER_DOMAIN': self.site_config.concurrent_requests or 5,
                })
                logger.info(f"Loaded configuration for {self.site_name}")
            else:
                logger.warning(f"No configuration found for {self.site_name}")
                
        except Exception as e:
            logger.error(f"Failed to load site configuration: {e}")
    
    def _load_category_mappings(self):
        """Load category mappings from JSON file"""
        try:
            import os
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
                'data', 'category_mappings.json'
            )
            
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.category_mappings = data.get('category_mappings', {})
            
            logger.info(f"Loaded {len(self.category_mappings)} category mappings")
            
        except Exception as e:
            logger.warning(f"Failed to load category mappings: {e}")
            self.category_mappings = {}
    
    def start_requests(self):
        """Generate initial requests"""
        if not self.site_config or not self.site_config.is_active:
            logger.warning(f"Site {self.site_name} is not active, skipping")
            return
        
        # Generate requests based on site configuration
        base_url = self.site_config.base_url
        
        # Start with main categories or search pages
        start_urls = self._get_start_urls()
        
        for url in start_urls:
            yield Request(
                url=url,
                callback=self.parse,
                meta={
                    'dont_cache': True,
                    'session_id': self.session_id
                },
                headers=self._get_headers()
            )
    
    def _get_start_urls(self):
        """Get start URLs for the spider"""
        base_url = self.site_config.base_url if self.site_config else self.start_urls[0]
        
        # Default start URLs - override in child spiders
        return [
            urljoin(base_url, '/'),
            urljoin(base_url, '/products/'),
            urljoin(base_url, '/shop/'),
            urljoin(base_url, '/category/'),
        ]
    
    def _get_headers(self):
        """Get headers for requests"""
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'fa-IR,fa;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        if self.site_config and self.site_config.user_agent:
            headers['User-Agent'] = self.site_config.user_agent
            
        return headers
    
    def parse(self, response):
        """Parse main page - override in child spiders"""
        # Extract product links
        product_links = self._extract_product_links(response)
        
        for link in product_links:
            yield Request(
                url=urljoin(response.url, link),
                callback=self.parse_product,
                meta={'session_id': self.session_id}
            )
        
        # Follow pagination
        next_page = self._extract_next_page(response)
        if next_page:
            yield Request(
                url=urljoin(response.url, next_page),
                callback=self.parse,
                meta={'session_id': self.session_id}
            )
    
    def parse_product(self, response):
        """Parse individual product page"""
        try:
            item = AutomotiveProductItem()
            
            # Extract basic information
            item['name'] = self._extract_name(response)
            item['price'] = self._extract_price(response)
            item['description'] = self._extract_description(response)
            item['category'] = self._extract_category(response)
            item['availability'] = self._extract_availability(response)
            item['main_image_url'] = self._extract_image_url(response)
            
            # Set metadata
            item['source_url'] = response.url
            item['site_name'] = self.site_name
            item['scraped_at'] = datetime.utcnow()
            item['spider_name'] = self.name
            item['currency'] = 'IRR'
            
            # Generate SKU if not available
            if not item.get('sku'):
                item['sku'] = self._generate_sku(item['name'], response.url)
            
            self.scraped_count += 1
            yield item
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"Error parsing product {response.url}: {e}")
    
    def _extract_product_links(self, response):
        """Extract product page links - override in child spiders"""
        if self.site_config and self.site_config.selectors:
            selector = self.site_config.selectors.get('product_link', 'a[href*="/product/"]')
        else:
            selector = 'a[href*="/product/"]'
        
        return response.css(selector + '::attr(href)').getall()
    
    def _extract_next_page(self, response):
        """Extract next page URL"""
        if self.site_config and self.site_config.selectors:
            selector = self.site_config.selectors.get('pagination', '.pagination a')
        else:
            selector = '.pagination a, .page-numbers a'
        
        next_links = response.css(selector + '::attr(href)').getall()
        # Find next page (usually contains 'next' or '>')
        for link in next_links:
            if any(word in link.lower() for word in ['next', 'بعدی', '>']):
                return link
        
        return None
    
    def _extract_name(self, response):
        """Extract product name"""
        if self.site_config and self.site_config.selectors:
            selector = self.site_config.selectors.get('title', 'h1')
        else:
            selector = 'h1, .product-title, .entry-title'
        
        name = response.css(selector + '::text').get()
        return name.strip() if name else None
    
    def _extract_price(self, response):
        """Extract product price"""
        if self.site_config and self.site_config.selectors:
            selector = self.site_config.selectors.get('price', '.price')
        else:
            selector = '.price, .product-price, .woocommerce-Price-amount'
        
        price_text = response.css(selector + '::text').get()
        if not price_text:
            # Try alternative selectors
            price_text = response.css(selector + ' bdi::text').get()
        
        if price_text:
            # Clean price text
            import re
            price_cleaned = re.sub(r'[^\d.,]', '', price_text)
            try:
                return float(price_cleaned.replace(',', ''))
            except:
                pass
        
        return None
    
    def _extract_description(self, response):
        """Extract product description"""
        selectors = [
            '.product-description::text',
            '.entry-content p::text',
            '.woocommerce-product-details__short-description::text',
            '.product-summary::text'
        ]
        
        for selector in selectors:
            desc = response.css(selector).get()
            if desc and len(desc.strip()) > 10:
                return desc.strip()
        
        return None
    
    def _extract_category(self, response):
        """Extract product category"""
        # Try breadcrumbs first
        breadcrumbs = response.css('.breadcrumb a::text, .breadcrumbs a::text').getall()
        if breadcrumbs and len(breadcrumbs) > 1:
            return breadcrumbs[-2]  # Second to last is usually category
        
        # Try category links
        category = response.css('.product-category a::text, .category-link::text').get()
        if category:
            return category.strip()
        
        return 'لوازم جانبی خودرو'  # Default category
    
    def _extract_availability(self, response):
        """Extract availability status"""
        if self.site_config and self.site_config.selectors:
            selector = self.site_config.selectors.get('availability', '.availability')
        else:
            selector = '.availability, .stock-status, .in-stock'
        
        availability = response.css(selector + '::text').get()
        if availability:
            availability = availability.strip().lower()
            if any(word in availability for word in ['موجود', 'available', 'in stock']):
                return 'موجود'
            elif any(word in availability for word in ['ناموجود', 'unavailable', 'out of stock']):
                return 'ناموجود'
        
        return 'نامشخص'
    
    def _extract_image_url(self, response):
        """Extract main product image URL"""
        selectors = [
            '.product-image img::attr(src)',
            '.wp-post-image::attr(src)',
            '.attachment-shop_single img::attr(src)',
            'img[alt*="product"]::attr(src)'
        ]
        
        for selector in selectors:
            img_url = response.css(selector).get()
            if img_url:
                return urljoin(response.url, img_url)
        
        return None
    
    def _generate_sku(self, name, url):
        """Generate SKU based on product name and URL"""
        import hashlib
        
        if name:
            # Use product name hash
            name_hash = hashlib.md5(name.encode('utf-8')).hexdigest()[:8]
            return f"{self.site_name.upper()}-{name_hash}"
        else:
            # Use URL hash
            url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()[:8]
            return f"{self.site_name.upper()}-{url_hash}"
    
    def closed(self, reason):
        """Spider closed callback"""
        end_time = datetime.utcnow()
        duration = (end_time - self.start_time).total_seconds()
        
        logger.info(f"Spider {self.name} finished:")
        logger.info(f"  Reason: {reason}")
        logger.info(f"  Duration: {duration:.2f} seconds")
        logger.info(f"  Items scraped: {self.scraped_count}")
        logger.info(f"  Errors: {self.error_count}")
