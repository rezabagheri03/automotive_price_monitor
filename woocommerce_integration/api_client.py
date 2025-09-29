"""
WooCommerce API client for product management
"""
import logging
import time
from typing import Dict, List, Optional, Union
import requests
from woocommerce import API
from config.settings import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)


class WooCommerceClient:
    """WooCommerce API client for product operations"""
    
    def __init__(self):
        self.config = Config()
        self.api = None
        self.session = requests.Session()
        self._init_api()
    
    def _init_api(self):
        """Initialize WooCommerce API client"""
        try:
            if not all([self.config.WOOCOMMERCE_URL, 
                       self.config.WOOCOMMERCE_CONSUMER_KEY, 
                       self.config.WOOCOMMERCE_CONSUMER_SECRET]):
                raise ValueError("WooCommerce credentials not configured")
            
            self.api = API(
                url=self.config.WOOCOMMERCE_URL,
                consumer_key=self.config.WOOCOMMERCE_CONSUMER_KEY,
                consumer_secret=self.config.WOOCOMMERCE_CONSUMER_SECRET,
                version=self.config.WOOCOMMERCE_API_VERSION,
                timeout=30,
                verify_ssl=True
            )
            
            # Test connection
            self.test_connection()
            logger.info("WooCommerce API client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize WooCommerce API: {e}")
            raise
    
    def test_connection(self) -> bool:
        """Test WooCommerce API connection"""
        try:
            response = self.api.get("products", params={"per_page": 1})
            return response.status_code == 200
        except Exception as e:
            logger.error(f"WooCommerce connection test failed: {e}")
            return False
    
    def get_products(self, per_page: int = 100, page: int = 1, **params) -> List[Dict]:
        """Get products from WooCommerce"""
        try:
            all_params = {
                "per_page": per_page,
                "page": page,
                **params
            }
            
            response = self.api.get("products", params=all_params)
            
            if response.status_code == 200:
                products = response.json()
                logger.info(f"Retrieved {len(products)} products from WooCommerce")
                return products
            else:
                logger.error(f"Failed to get products: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting products from WooCommerce: {e}")
            return []
    
    def get_all_products(self) -> List[Dict]:
        """Get all products with pagination"""
        all_products = []
        page = 1
        per_page = 100
        
        while True:
            products = self.get_products(per_page=per_page, page=page)
            
            if not products:
                break
            
            all_products.extend(products)
            
            # If we got less than per_page, we've reached the end
            if len(products) < per_page:
                break
                
            page += 1
            time.sleep(0.5)  # Rate limiting
        
        logger.info(f"Retrieved {len(all_products)} total products from WooCommerce")
        return all_products
    
    def create_product(self, product_data: Dict) -> Optional[Dict]:
        """Create a new product in WooCommerce"""
        try:
            response = self.api.post("products", product_data)
            
            if response.status_code == 201:
                product = response.json()
                logger.info(f"Created product: {product.get('name')} (ID: {product.get('id')})")
                return product
            else:
                logger.error(f"Failed to create product: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating product in WooCommerce: {e}")
            return None
    
    def update_product(self, product_id: int, product_data: Dict) -> Optional[Dict]:
        """Update an existing product in WooCommerce"""
        try:
            response = self.api.put(f"products/{product_id}", product_data)
            
            if response.status_code == 200:
                product = response.json()
                logger.info(f"Updated product ID {product_id}: {product.get('name')}")
                return product
            else:
                logger.error(f"Failed to update product {product_id}: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error updating product {product_id} in WooCommerce: {e}")
            return None
    
    def update_product_price(self, product_id: int, price: Union[float, str]) -> bool:
        """Update only the price of a product"""
        try:
            price_data = {
                "regular_price": str(price)
            }
            
            result = self.update_product(product_id, price_data)
            return result is not None
            
        except Exception as e:
            logger.error(f"Error updating price for product {product_id}: {e}")
            return False
    
    def batch_update_products(self, updates: List[Dict]) -> Dict:
        """Batch update multiple products"""
        results = {
            'success': 0,
            'failed': 0,
            'errors': []
        }
        
        try:
            # WooCommerce supports batch operations
            batch_data = {
                'update': updates
            }
            
            response = self.api.post("products/batch", batch_data)
            
            if response.status_code == 200:
                batch_result = response.json()
                
                # Process results
                if 'update' in batch_result:
                    for item in batch_result['update']:
                        if 'error' in item:
                            results['failed'] += 1
                            results['errors'].append(f"Product {item.get('id')}: {item['error']['message']}")
                        else:
                            results['success'] += 1
                
                logger.info(f"Batch update completed: {results['success']} success, {results['failed']} failed")
            else:
                logger.error(f"Batch update failed: {response.status_code} - {response.text}")
                results['errors'].append(f"API Error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error in batch update: {e}")
            results['errors'].append(str(e))
        
        return results
    
    def delete_product(self, product_id: int, force: bool = False) -> bool:
        """Delete a product from WooCommerce"""
        try:
            params = {"force": force} if force else {}
            response = self.api.delete(f"products/{product_id}", params=params)
            
            success = response.status_code in [200, 201]
            if success:
                logger.info(f"Deleted product ID {product_id}")
            else:
                logger.error(f"Failed to delete product {product_id}: {response.status_code}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error deleting product {product_id}: {e}")
            return False
    
    def get_product_categories(self) -> List[Dict]:
        """Get all product categories from WooCommerce"""
        try:
            response = self.api.get("products/categories", params={"per_page": 100})
            
            if response.status_code == 200:
                categories = response.json()
                logger.info(f"Retrieved {len(categories)} categories from WooCommerce")
                return categories
            else:
                logger.error(f"Failed to get categories: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting categories from WooCommerce: {e}")
            return []
    
    def create_category(self, category_data: Dict) -> Optional[Dict]:
        """Create a new product category"""
        try:
            response = self.api.post("products/categories", category_data)
            
            if response.status_code == 201:
                category = response.json()
                logger.info(f"Created category: {category.get('name')} (ID: {category.get('id')})")
                return category
            else:
                logger.error(f"Failed to create category: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating category: {e}")
            return None
    
    def search_products(self, search_term: str, per_page: int = 50) -> List[Dict]:
        """Search for products by name or SKU"""
        try:
            params = {
                "search": search_term,
                "per_page": per_page
            }
            
            response = self.api.get("products", params=params)
            
            if response.status_code == 200:
                products = response.json()
                logger.info(f"Found {len(products)} products matching '{search_term}'")
                return products
            else:
                logger.error(f"Search failed: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error searching products: {e}")
            return []
    
    def get_product_by_sku(self, sku: str) -> Optional[Dict]:
        """Get product by SKU"""
        try:
            params = {
                "sku": sku,
                "per_page": 1
            }
            
            response = self.api.get("products", params=params)
            
            if response.status_code == 200:
                products = response.json()
                if products:
                    return products[0]
                else:
                    logger.info(f"No product found with SKU: {sku}")
                    return None
            else:
                logger.error(f"Failed to get product by SKU: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting product by SKU {sku}: {e}")
            return None
    
    def update_stock_status(self, product_id: int, stock_status: str, stock_quantity: int = None) -> bool:
        """Update stock status and quantity"""
        try:
            stock_data = {
                "stock_status": stock_status,  # 'instock', 'outofstock', 'onbackorder'
                "manage_stock": stock_quantity is not None
            }
            
            if stock_quantity is not None:
                stock_data["stock_quantity"] = stock_quantity
            
            result = self.update_product(product_id, stock_data)
            return result is not None
            
        except Exception as e:
            logger.error(f"Error updating stock for product {product_id}: {e}")
            return False
    
    def get_orders(self, status: str = None, per_page: int = 50) -> List[Dict]:
        """Get orders from WooCommerce"""
        try:
            params = {"per_page": per_page}
            if status:
                params["status"] = status
            
            response = self.api.get("orders", params=params)
            
            if response.status_code == 200:
                orders = response.json()
                logger.info(f"Retrieved {len(orders)} orders from WooCommerce")
                return orders
            else:
                logger.error(f"Failed to get orders: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting orders from WooCommerce: {e}")
            return []
    
    def get_api_info(self) -> Dict:
        """Get WooCommerce API information"""
        try:
            response = self.api.get("")
            
            if response.status_code == 200:
                info = response.json()
                return {
                    'store_url': self.config.WOOCOMMERCE_URL,
                    'api_version': self.config.WOOCOMMERCE_API_VERSION,
                    'connection_status': 'Connected',
                    'store_info': info
                }
            else:
                return {
                    'store_url': self.config.WOOCOMMERCE_URL,
                    'api_version': self.config.WOOCOMMERCE_API_VERSION,
                    'connection_status': f'Error: {response.status_code}',
                    'store_info': {}
                }
                
        except Exception as e:
            return {
                'store_url': self.config.WOOCOMMERCE_URL,
                'api_version': self.config.WOOCOMMERCE_API_VERSION,
                'connection_status': f'Error: {str(e)}',
                'store_info': {}
            }
    
    def validate_product_data(self, product_data: Dict) -> Tuple[bool, List[str]]:
        """Validate product data before sending to WooCommerce"""
        errors = []
        
        # Required fields
        required_fields = ['name']
        for field in required_fields:
            if not product_data.get(field):
                errors.append(f"Missing required field: {field}")
        
        # Validate price
        if 'regular_price' in product_data:
            try:
                price = float(product_data['regular_price'])
                if price < 0:
                    errors.append("Price cannot be negative")
            except (ValueError, TypeError):
                errors.append("Invalid price format")
        
        # Validate SKU uniqueness (if provided)
        if product_data.get('sku'):
            existing_product = self.get_product_by_sku(product_data['sku'])
            if existing_product and existing_product.get('id') != product_data.get('id'):
                errors.append(f"SKU '{product_data['sku']}' already exists")
        
        return len(errors) == 0, errors
