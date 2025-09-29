"""
Batch processing for WooCommerce operations
"""
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from .api_client import WooCommerceClient
from database.models import Product, PriceHistory
from config.database import db_manager
from utils.logger import setup_logger

logger = setup_logger(__name__)


class BatchProcessor:
    """Handle batch operations for WooCommerce"""
    
    def __init__(self, max_workers: int = 5, rate_limit: float = 0.5):
        self.wc_client = WooCommerceClient()
        self.db_manager = db_manager
        self.max_workers = max_workers
        self.rate_limit = rate_limit  # Seconds between requests
        self.last_request_time = 0
    
    def _rate_limit_delay(self):
        """Apply rate limiting between requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit:
            sleep_time = self.rate_limit - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def batch_update_prices(self, price_type: str = 'avg', batch_size: int = 50) -> Dict:
        """Batch update prices for all products"""
        logger.info(f"Starting batch price update with {price_type} prices")
        
        results = {
            'total_products': 0,
            'processed': 0,
            'updated': 0,
            'failed': 0,
            'skipped': 0,
            'errors': [],
            'duration': 0,
            'start_time': datetime.utcnow()
        }
        
        try:
            # Get products that need price updates
            products_to_update = self._get_products_for_price_update(price_type)
            results['total_products'] = len(products_to_update)
            
            if not products_to_update:
                logger.info("No products found for price update")
                return results
            
            # Process in batches
            for i in range(0, len(products_to_update), batch_size):
                batch = products_to_update[i:i + batch_size]
                batch_results = self._process_price_batch(batch, price_type)
                
                # Aggregate results
                results['processed'] += batch_results['processed']
                results['updated'] += batch_results['updated']
                results['failed'] += batch_results['failed']
                results['skipped'] += batch_results['skipped']
                results['errors'].extend(batch_results['errors'])
                
                logger.info(f"Processed batch {i//batch_size + 1}: {len(batch)} products")
                
                # Rate limiting between batches
                if i + batch_size < len(products_to_update):
                    time.sleep(1)
            
            # Calculate duration
            results['duration'] = (datetime.utcnow() - results['start_time']).total_seconds()
            
            logger.info(f"Batch price update completed: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Batch price update failed: {e}")
            results['errors'].append(f"Batch processing failed: {str(e)}")
            return results
    
    def _get_products_for_price_update(self, price_type: str) -> List[Dict]:
        """Get products that need price updates"""
        try:
            with self.db_manager.get_session() as session:
                # Query to get products with latest prices and WooCommerce mapping
                query = """
                SELECT 
                    p.id,
                    p.name,
                    p.woocommerce_id,
                    ph.avg_price,
                    ph.min_price,
                    ph.max_price,
                    ph.scraped_at
                FROM products p
                JOIN (
                    SELECT DISTINCT
                        product_id,
                        FIRST_VALUE(avg_price) OVER (PARTITION BY product_id ORDER BY scraped_at DESC) as avg_price,
                        FIRST_VALUE(min_price) OVER (PARTITION BY product_id ORDER BY scraped_at DESC) as min_price,
                        FIRST_VALUE(max_price) OVER (PARTITION BY product_id ORDER BY scraped_at DESC) as max_price,
                        FIRST_VALUE(scraped_at) OVER (PARTITION BY product_id ORDER BY scraped_at DESC) as scraped_at,
                        ROW_NUMBER() OVER (PARTITION BY product_id ORDER BY scraped_at DESC) as rn
                    FROM price_history
                    WHERE avg_price IS NOT NULL
                ) ph ON p.id = ph.product_id AND ph.rn = 1
                WHERE p.is_active = 1 
                  AND p.is_monitored = 1
                  AND p.woocommerce_id IS NOT NULL
                ORDER BY p.id
                """
                
                result = session.execute(query).fetchall()
                
                products = []
                for row in result:
                    # Select price based on type
                    if price_type == 'avg':
                        price = row.avg_price
                    elif price_type == 'min':
                        price = row.min_price
                    elif price_type == 'max':
                        price = row.max_price
                    else:
                        price = row.avg_price
                    
                    if price:
                        products.append({
                            'id': row.id,
                            'name': row.name,
                            'woocommerce_id': row.woocommerce_id,
                            'price': float(price),
                            'last_updated': row.scraped_at
                        })
                
                logger.info(f"Found {len(products)} products for price update")
                return products
                
        except Exception as e:
            logger.error(f"Error getting products for price update: {e}")
            return []
    
    def _process_price_batch(self, batch: List[Dict], price_type: str) -> Dict:
        """Process a batch of price updates"""
        results = {
            'processed': 0,
            'updated': 0,
            'failed': 0,
            'skipped': 0,
            'errors': []
        }
        
        # Prepare batch data for WooCommerce API
        wc_updates = []
        
        for product in batch:
            try:
                wc_updates.append({
                    'id': product['woocommerce_id'],
                    'regular_price': str(int(product['price']))  # Convert to integer string
                })
                results['processed'] += 1
                
            except Exception as e:
                results['failed'] += 1
                results['errors'].append(f"Product {product['name']}: {str(e)}")
        
        # Send batch update to WooCommerce
        if wc_updates:
            try:
                self._rate_limit_delay()
                batch_result = self.wc_client.batch_update_products(wc_updates)
                
                results['updated'] += batch_result.get('success', 0)
                results['failed'] += batch_result.get('failed', 0)
                results['errors'].extend(batch_result.get('errors', []))
                
            except Exception as e:
                logger.error(f"Batch WooCommerce update failed: {e}")
                results['failed'] += len(wc_updates)
                results['errors'].append(f"WooCommerce batch update failed: {str(e)}")
        
        return results
    
    def sync_products_from_woocommerce(self) -> Dict:
        """Sync products from WooCommerce to database"""
        logger.info("Starting product sync from WooCommerce")
        
        results = {
            'total_wc_products': 0,
            'new_products': 0,
            'updated_mappings': 0,
            'errors': [],
            'duration': 0,
            'start_time': datetime.utcnow()
        }
        
        try:
            # Get all products from WooCommerce
            wc_products = self.wc_client.get_all_products()
            results['total_wc_products'] = len(wc_products)
            
            if not wc_products:
                logger.warning("No products found in WooCommerce")
                return results
            
            # Process each WooCommerce product
            for wc_product in wc_products:
                try:
                    self._sync_single_product(wc_product, results)
                except Exception as e:
                    results['errors'].append(f"Product {wc_product.get('name', 'Unknown')}: {str(e)}")
            
            # Calculate duration
            results['duration'] = (datetime.utcnow() - results['start_time']).total_seconds()
            
            logger.info(f"Product sync completed: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Product sync failed: {e}")
            results['errors'].append(f"Sync failed: {str(e)}")
            return results
    
    def _sync_single_product(self, wc_product: Dict, results: Dict):
        """Sync a single product from WooCommerce"""
        try:
            with self.db_manager.get_session() as session:
                # Try to find existing product by WooCommerce ID
                existing_product = session.query(Product).filter(
                    Product.woocommerce_id == wc_product['id']
                ).first()
                
                if existing_product:
                    # Update existing mapping
                    existing_product.name = wc_product['name']
                    existing_product.description = wc_product.get('description', '')
                    existing_product.updated_at = datetime.utcnow()
                    results['updated_mappings'] += 1
                else:
                    # Try to find by name similarity
                    similar_product = session.query(Product).filter(
                        Product.name.like(f"%{wc_product['name'][:20]}%")
                    ).first()
                    
                    if similar_product and not similar_product.woocommerce_id:
                        # Link existing product
                        similar_product.woocommerce_id = wc_product['id']
                        similar_product.updated_at = datetime.utcnow()
                        results['updated_mappings'] += 1
                    else:
                        # Create new product entry
                        new_product = Product(
                            name=wc_product['name'],
                            description=wc_product.get('description', ''),
                            woocommerce_id=wc_product['id'],
                            category='لوازم جانبی خودرو',  # Default category
                            is_active=True,
                            is_monitored=False,  # Don't monitor WooCommerce-only products
                            created_at=datetime.utcnow()
                        )
                        session.add(new_product)
                        results['new_products'] += 1
                        
        except Exception as e:
            logger.error(f"Error syncing product {wc_product.get('name', 'Unknown')}: {e}")
            raise
    
    def bulk_update_stock_status(self, stock_updates: List[Dict]) -> Dict:
        """Bulk update stock status for multiple products"""
        logger.info(f"Starting bulk stock status update for {len(stock_updates)} products")
        
        results = {
            'total_updates': len(stock_updates),
            'successful': 0,
            'failed': 0,
            'errors': []
        }
        
        def update_single_stock(update_data):
            try:
                self._rate_limit_delay()
                success = self.wc_client.update_stock_status(
                    update_data['product_id'],
                    update_data['stock_status'],
                    update_data.get('stock_quantity')
                )
                return {'success': success, 'product_id': update_data['product_id']}
            except Exception as e:
                return {'success': False, 'product_id': update_data['product_id'], 'error': str(e)}
        
        # Use thread pool for concurrent updates
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_update = {executor.submit(update_single_stock, update): update for update in stock_updates}
            
            for future in as_completed(future_to_update):
                update_data = future_to_update[future]
                try:
                    result = future.result()
                    if result['success']:
                        results['successful'] += 1
                    else:
                        results['failed'] += 1
                        error_msg = result.get('error', 'Unknown error')
                        results['errors'].append(f"Product {result['product_id']}: {error_msg}")
                        
                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append(f"Product {update_data['product_id']}: {str(e)}")
        
        logger.info(f"Bulk stock update completed: {results['successful']} successful, {results['failed']} failed")
        return results
    
    def cleanup_orphaned_mappings(self) -> Dict:
        """Clean up products with WooCommerce IDs that no longer exist"""
        logger.info("Starting cleanup of orphaned WooCommerce mappings")
        
        results = {
            'checked_products': 0,
            'orphaned_found': 0,
            'cleaned_up': 0,
            'errors': []
        }
        
        try:
            with self.db_manager.get_session() as session:
                # Get all products with WooCommerce IDs
                mapped_products = session.query(Product).filter(
                    Product.woocommerce_id.isnot(None)
                ).all()
                
                results['checked_products'] = len(mapped_products)
                
                for product in mapped_products:
                    try:
                        # Check if product still exists in WooCommerce
                        wc_products = self.wc_client.get_products(per_page=1, include=[product.woocommerce_id])
                        
                        if not wc_products or not any(p['id'] == product.woocommerce_id for p in wc_products):
                            # Product no longer exists in WooCommerce
                            results['orphaned_found'] += 1
                            
                            # Remove WooCommerce ID mapping
                            product.woocommerce_id = None
                            product.updated_at = datetime.utcnow()
                            results['cleaned_up'] += 1
                            
                            logger.info(f"Cleaned up orphaned mapping for product: {product.name}")
                        
                        # Rate limiting
                        self._rate_limit_delay()
                        
                    except Exception as e:
                        results['errors'].append(f"Error checking product {product.name}: {str(e)}")
                
                logger.info(f"Cleanup completed: {results}")
                return results
                
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            results['errors'].append(f"Cleanup failed: {str(e)}")
            return results
    
    def generate_batch_report(self, operation_type: str, results: Dict) -> str:
        """Generate a report for batch operations"""
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        
        report = f"""
=== Batch Operation Report ===
Operation Type: {operation_type}
Timestamp: {timestamp}
Duration: {results.get('duration', 0):.2f} seconds

Summary:
- Total Items: {results.get('total_products', results.get('total_updates', results.get('checked_products', 0)))}
- Successful: {results.get('updated', results.get('successful', results.get('cleaned_up', 0)))}
- Failed: {results.get('failed', 0)}
- Skipped: {results.get('skipped', 0)}

"""
        
        if results.get('errors'):
            report += f"Errors ({len(results['errors'])}):\n"
            for error in results['errors'][:10]:  # Limit to first 10 errors
                report += f"- {error}\n"
            
            if len(results['errors']) > 10:
                report += f"... and {len(results['errors']) - 10} more errors\n"
        
        return report
