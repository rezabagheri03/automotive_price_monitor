"""
Item pipelines for automotive scraper
"""
import logging
from datetime import datetime
from itemadapter import ItemAdapter
from sqlalchemy.exc import SQLAlchemyError
from database.models import Product, PriceHistory, ScrapingLog
from config.database import db_manager
from .items import AutomotiveProductItem, PriceHistoryItem

logger = logging.getLogger(__name__)


class ValidationPipeline:
    """Validate scraped items before processing"""
    
    def __init__(self):
        self.required_fields = ['name', 'price', 'site_name', 'source_url']
        self.processed_items = 0
        self.dropped_items = 0
    
    def process_item(self, item, spider):
        """Validate item data"""
        adapter = ItemAdapter(item)
        
        # Check required fields
        missing_fields = []
        for field in self.required_fields:
            if not adapter.get(field):
                missing_fields.append(field)
        
        if missing_fields:
            self.dropped_items += 1
            raise DropItem(f"Missing required fields: {missing_fields}")
        
        # Validate price
        price = adapter.get('price')
        if price is not None:
            try:
                price = float(price)
                if price <= 0:
                    self.dropped_items += 1
                    raise DropItem(f"Invalid price: {price}")
                adapter['price'] = price
            except (ValueError, TypeError):
                self.dropped_items += 1
                raise DropItem(f"Cannot convert price to float: {price}")
        
        # Validate URL
        url = adapter.get('source_url')
        if url and not url.startswith(('http://', 'https://')):
            self.dropped_items += 1
            raise DropItem(f"Invalid URL: {url}")
        
        # Clean and validate name
        name = adapter.get('name', '').strip()
        if len(name) < 3:
            self.dropped_items += 1
            raise DropItem(f"Product name too short: {name}")
        adapter['name'] = name
        
        # Set default values
        if not adapter.get('scraped_at'):
            adapter['scraped_at'] = datetime.utcnow()
        
        if not adapter.get('currency'):
            adapter['currency'] = 'IRR'
        
        if not adapter.get('availability'):
            adapter['availability'] = 'unknown'
        
        self.processed_items += 1
        return item
    
    def close_spider(self, spider):
        """Log pipeline statistics"""
        logger.info(f"ValidationPipeline - Processed: {self.processed_items}, Dropped: {self.dropped_items}")


class DatabasePipeline:
    """Save items to database"""
    
    def __init__(self):
        self.db_manager = db_manager
        self.saved_items = 0
        self.failed_items = 0
    
    def open_spider(self, spider):
        """Initialize database connection"""
        if not self.db_manager.test_connection():
            raise Exception("Database connection failed")
        logger.info("DatabasePipeline - Connected to database")
    
    def close_spider(self, spider):
        """Close database connections and log statistics"""
        logger.info(f"DatabasePipeline - Saved: {self.saved_items}, Failed: {self.failed_items}")
    
    def process_item(self, item, spider):
        """Save item to database"""
        adapter = ItemAdapter(item)
        
        try:
            with self.db_manager.get_session() as session:
                if isinstance(item, AutomotiveProductItem):
                    self._save_product(session, adapter, spider)
                elif isinstance(item, PriceHistoryItem):
                    self._save_price_history(session, adapter, spider)
                
                self.saved_items += 1
                
        except Exception as e:
            self.failed_items += 1
            logger.error(f"Failed to save item to database: {e}")
            logger.error(f"Item data: {dict(adapter)}")
        
        return item
    
    def _save_product(self, session, adapter, spider):
        """Save product to database"""
        # Check if product already exists
        existing_product = session.query(Product).filter(
            Product.name == adapter['name'],
            Product.site_urls.contains(adapter['source_url'])
        ).first()
        
        if existing_product:
            # Update existing product
            existing_product.description = adapter.get('description') or existing_product.description
            existing_product.image_url = adapter.get('main_image_url') or existing_product.image_url
            existing_product.last_scraped = adapter.get('scraped_at')
            existing_product.updated_at = datetime.utcnow()
            
            # Update site URLs
            site_urls = existing_product.site_urls or {}
            site_urls[adapter['site_name']] = adapter['source_url']
            existing_product.site_urls = site_urls
            
            product = existing_product
        else:
            # Create new product
            product = Product(
                name=adapter['name'],
                sku=adapter.get('sku'),
                category=adapter.get('category', 'لوازم جانبی خودرو'),
                description=adapter.get('description'),
                image_url=adapter.get('main_image_url'),
                site_urls={adapter['site_name']: adapter['source_url']},
                is_active=True,
                is_monitored=True,
                created_at=datetime.utcnow(),
                last_scraped=adapter.get('scraped_at')
            )
            session.add(product)
            session.flush()  # Get the ID
        
        # Save price history
        price_history = PriceHistory(
            product_id=product.id,
            site_name=adapter['site_name'],
            site_price=adapter['price'],
            site_url=adapter['source_url'],
            site_availability=adapter.get('in_stock', True),
            currency=adapter.get('currency', 'IRR'),
            scraped_at=adapter.get('scraped_at')
        )
        session.add(price_history)
    
    def _save_price_history(self, session, adapter, spider):
        """Save price history entry"""
        # Find product by name and site
        product = session.query(Product).filter(
            Product.name == adapter['product_name']
        ).first()
        
        if not product:
            logger.warning(f"Product not found for price history: {adapter['product_name']}")
            return
        
        price_history = PriceHistory(
            product_id=product.id,
            site_name=adapter['site_name'],
            site_price=adapter['price'],
            site_url=adapter['source_url'],
            currency=adapter.get('currency', 'IRR'),
            scraped_at=adapter.get('scraped_at')
        )
        session.add(price_history)


class DuplicatesPipeline:
    """Filter out duplicate items"""
    
    def __init__(self):
        self.seen_items = set()
        self.duplicate_count = 0
    
    def process_item(self, item, spider):
        """Check for duplicates"""
        adapter = ItemAdapter(item)
        
        # Create unique key based on name and site
        unique_key = f"{adapter.get('name', '').strip()}|{adapter.get('site_name', '')}"
        
        if unique_key in self.seen_items:
            self.duplicate_count += 1
            raise DropItem(f"Duplicate item found: {unique_key}")
        
        self.seen_items.add(unique_key)
        return item
    
    def close_spider(self, spider):
        """Log duplicate statistics"""
        logger.info(f"DuplicatesPipeline - Filtered {self.duplicate_count} duplicates")


class CleaningPipeline:
    """Clean and normalize item data"""
    
    def process_item(self, item, spider):
        """Clean item data"""
        adapter = ItemAdapter(item)
        
        # Clean name
        if adapter.get('name'):
            name = adapter['name'].strip()
            # Remove extra spaces
            name = ' '.join(name.split())
            adapter['name'] = name
        
        # Clean description
        if adapter.get('description'):
            desc = adapter['description'].strip()
            # Remove extra spaces and limit length
            desc = ' '.join(desc.split())[:500]
            adapter['description'] = desc
        
        # Normalize availability
        availability = adapter.get('availability', '').lower()
        if any(word in availability for word in ['موجود', 'available', 'in stock']):
            adapter['in_stock'] = True
        elif any(word in availability for word in ['ناموجود', 'unavailable', 'out of stock']):
            adapter['in_stock'] = False
        else:
            adapter['in_stock'] = True  # Default to available
        
        # Clean category
        if adapter.get('category'):
            category = adapter['category'].strip()
            adapter['category'] = category
        
        return item


class StatsPipeline:
    """Collect scraping statistics"""
    
    def __init__(self):
        self.stats = {
            'items_scraped': 0,
            'items_saved': 0,
            'items_failed': 0,
            'sites': {},
            'categories': {},
            'start_time': None,
            'end_time': None
        }
    
    def open_spider(self, spider):
        """Initialize statistics"""
        self.stats['start_time'] = datetime.utcnow()
        self.stats['spider_name'] = spider.name
    
    def process_item(self, item, spider):
        """Update statistics"""
        adapter = ItemAdapter(item)
        
        self.stats['items_scraped'] += 1
        
        # Track by site
        site = adapter.get('site_name', 'unknown')
        if site not in self.stats['sites']:
            self.stats['sites'][site] = 0
        self.stats['sites'][site] += 1
        
        # Track by category
        category = adapter.get('category', 'unknown')
        if category not in self.stats['categories']:
            self.stats['categories'][category] = 0
        self.stats['categories'][category] += 1
        
        return item
    
    def close_spider(self, spider):
        """Finalize and save statistics"""
        self.stats['end_time'] = datetime.utcnow()
        
        if self.stats['start_time']:
            duration = self.stats['end_time'] - self.stats['start_time']
            self.stats['duration_seconds'] = duration.total_seconds()
        
        # Log final statistics
        logger.info("=== Scraping Statistics ===")
        logger.info(f"Items scraped: {self.stats['items_scraped']}")
        logger.info(f"Duration: {self.stats.get('duration_seconds', 0):.2f} seconds")
        logger.info(f"Sites: {self.stats['sites']}")
        logger.info(f"Categories: {self.stats['categories']}")
        
        # Save to database
        self._save_stats_to_db(spider)
    
    def _save_stats_to_db(self, spider):
        """Save statistics to database"""
        try:
            with db_manager.get_session() as session:
                scraping_log = ScrapingLog(
                    session_id=getattr(spider, 'session_id', 'unknown'),
                    site_name=','.join(self.stats['sites'].keys()),
                    spider_name=spider.name,
                    status='completed',
                    products_found=self.stats['items_scraped'],
                    products_scraped=self.stats['items_scraped'],
                    start_time=self.stats['start_time'],
                    end_time=self.stats['end_time'],
                    duration_seconds=int(self.stats.get('duration_seconds', 0))
                )
                session.add(scraping_log)
                
        except Exception as e:
            logger.error(f"Failed to save statistics to database: {e}")


# Import DropItem at the end to avoid circular imports
from scrapy.exceptions import DropItem
