"""
CSV import functionality for WooCommerce products
"""
import csv
import os
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import pandas as pd
from .api_client import WooCommerceClient
from database.models import Product
from config.database import db_manager
from utils.logger import setup_logger

logger = setup_logger(__name__)


class CSVImporter:
    """Handle CSV import to WooCommerce"""
    
    def __init__(self):
        self.wc_client = WooCommerceClient()
        self.db_manager = db_manager
    
    def import_csv_to_woocommerce(self, csv_path: str, price_type: str = 'avg', 
                                 dry_run: bool = False) -> Dict:
        """Import CSV file to WooCommerce"""
        logger.info(f"Starting CSV import: {csv_path} (price_type: {price_type}, dry_run: {dry_run})")
        
        results = {
            'total_rows': 0,
            'processed': 0,
            'created': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0,
            'error_details': [],
            'duration': 0,
            'dry_run': dry_run
        }
        
        start_time = datetime.utcnow()
        
        try:
            # Read CSV file
            products_data = self._read_csv_file(csv_path)
            if not products_data:
                raise ValueError("No data found in CSV file")
            
            results['total_rows'] = len(products_data)
            
            # Process each product
            for i, product_data in enumerate(products_data):
                try:
                    # Validate data
                    is_valid, validation_errors = self._validate_csv_row(product_data)
                    if not is_valid:
                        results['errors'] += 1
                        results['error_details'].append(f"Row {i+1}: {', '.join(validation_errors)}")
                        continue
                    
                    # Convert to WooCommerce format
                    wc_product_data = self._convert_to_woocommerce_format(product_data)
                    
                    # Check if product exists
                    existing_product = self._find_existing_product(wc_product_data)
                    
                    if not dry_run:
                        if existing_product:
                            # Update existing product
                            success = self._update_woocommerce_product(existing_product['id'], wc_product_data)
                            if success:
                                results['updated'] += 1
                                self._update_database_mapping(wc_product_data, existing_product['id'])
                            else:
                                results['errors'] += 1
                                results['error_details'].append(f"Failed to update product: {wc_product_data['name']}")
                        else:
                            # Create new product
                            created_product = self._create_woocommerce_product(wc_product_data)
                            if created_product:
                                results['created'] += 1
                                self._update_database_mapping(wc_product_data, created_product['id'])
                            else:
                                results['errors'] += 1
                                results['error_details'].append(f"Failed to create product: {wc_product_data['name']}")
                    else:
                        # Dry run - just count what would happen
                        if existing_product:
                            results['updated'] += 1
                        else:
                            results['created'] += 1
                    
                    results['processed'] += 1
                    
                    # Progress logging
                    if (i + 1) % 50 == 0:
                        logger.info(f"Processed {i + 1}/{len(products_data)} products")
                    
                except Exception as e:
                    results['errors'] += 1
                    results['error_details'].append(f"Row {i+1}: {str(e)}")
                    logger.error(f"Error processing row {i+1}: {e}")
            
            # Calculate duration
            end_time = datetime.utcnow()
            results['duration'] = (end_time - start_time).total_seconds()
            
            logger.info(f"CSV import completed: {results}")
            return results
            
        except Exception as e:
            logger.error(f"CSV import failed: {e}")
            results['error_details'].append(f"Import failed: {str(e)}")
            return results
    
    def _read_csv_file(self, csv_path: str) -> List[Dict]:
        """Read CSV file and return list of dictionaries"""
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        
        try:
            # Try different encodings
            encodings = ['utf-8-sig', 'utf-8', 'cp1256', 'iso-8859-1']
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(csv_path, encoding=encoding)
                    logger.info(f"Successfully read CSV with encoding: {encoding}")
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise ValueError("Could not read CSV file with any supported encoding")
            
            # Convert to list of dictionaries
            products_data = df.to_dict('records')
            
            # Clean data
            for product in products_data:
                for key, value in product.items():
                    if pd.isna(value):
                        product[key] = ''
                    else:
                        product[key] = str(value).strip()
            
            logger.info(f"Read {len(products_data)} products from CSV")
            return products_data
            
        except Exception as e:
            logger.error(f"Error reading CSV file: {e}")
            raise
    
    def _validate_csv_row(self, row_data: Dict) -> Tuple[bool, List[str]]:
        """Validate CSV row data"""
        errors = []
        
        # Check required fields
        required_fields = ['name', 'price']
        for field in required_fields:
            if not row_data.get(field):
                errors.append(f"Missing required field: {field}")
        
        # Validate price
        try:
            price = float(row_data.get('price', 0))
            if price <= 0:
                errors.append("Price must be greater than 0")
        except (ValueError, TypeError):
            errors.append("Invalid price format")
        
        # Validate name length
        name = row_data.get('name', '')
        if len(name) < 3:
            errors.append("Product name too short")
        elif len(name) > 255:
            errors.append("Product name too long")
        
        return len(errors) == 0, errors
    
    def _convert_to_woocommerce_format(self, csv_data: Dict) -> Dict:
        """Convert CSV data to WooCommerce product format"""
        wc_data = {
            'name': csv_data.get('name', ''),
            'regular_price': str(csv_data.get('price', '')),
            'description': csv_data.get('description', ''),
            'short_description': csv_data.get('description', '')[:160] + '...' if len(csv_data.get('description', '')) > 160 else csv_data.get('description', ''),
            'status': 'publish',
            'catalog_visibility': 'visible',
            'manage_stock': False,
            'stock_status': 'instock'
        }
        
        # Add category
        if csv_data.get('category'):
            wc_data['categories'] = [{'name': csv_data['category']}]
        
        # Add image
        if csv_data.get('image'):
            wc_data['images'] = [{'src': csv_data['image']}]
        
        # Add SKU if available
        if csv_data.get('sku'):
            wc_data['sku'] = csv_data['sku']
        
        return wc_data
    
    def _find_existing_product(self, product_data: Dict) -> Optional[Dict]:
        """Find existing product in WooCommerce"""
        # Try to find by SKU first
        if product_data.get('sku'):
            existing = self.wc_client.get_product_by_sku(product_data['sku'])
            if existing:
                return existing
        
        # Try to find by name
        search_results = self.wc_client.search_products(product_data['name'], per_page=5)
        
        for product in search_results:
            if product['name'].lower().strip() == product_data['name'].lower().strip():
                return product
        
        return None
    
    def _create_woocommerce_product(self, product_data: Dict) -> Optional[Dict]:
        """Create new product in WooCommerce"""
        try:
            return self.wc_client.create_product(product_data)
        except Exception as e:
            logger.error(f"Error creating WooCommerce product: {e}")
            return None
    
    def _update_woocommerce_product(self, product_id: int, product_data: Dict) -> bool:
        """Update existing product in WooCommerce"""
        try:
            # Only update price and description to avoid conflicts
            update_data = {
                'regular_price': product_data.get('regular_price'),
                'description': product_data.get('description', ''),
            }
            
            result = self.wc_client.update_product(product_id, update_data)
            return result is not None
        except Exception as e:
            logger.error(f"Error updating WooCommerce product {product_id}: {e}")
            return False
    
    def _update_database_mapping(self, csv_data: Dict, wc_product_id: int):
        """Update database with WooCommerce product ID mapping"""
        try:
            with self.db_manager.get_session() as session:
                # Find product in database by name
                product = session.query(Product).filter(
                    Product.name == csv_data['name']
                ).first()
                
                if product:
                    product.woocommerce_id = wc_product_id
                    product.updated_at = datetime.utcnow()
                    logger.debug(f"Updated database mapping for product {product.name} -> WC ID {wc_product_id}")
                
        except Exception as e:
            logger.error(f"Error updating database mapping: {e}")
    
    def validate_csv_file(self, csv_path: str) -> Dict:
        """Validate CSV file format and content"""
        validation_result = {
            'valid': False,
            'total_rows': 0,
            'valid_rows': 0,
            'errors': [],
            'warnings': [],
            'sample_data': []
        }
        
        try:
            # Read CSV file
            products_data = self._read_csv_file(csv_path)
            validation_result['total_rows'] = len(products_data)
            
            # Check required columns
            if products_data:
                sample_row = products_data[0]
                required_columns = ['name', 'price']
                missing_columns = [col for col in required_columns if col not in sample_row]
                
                if missing_columns:
                    validation_result['errors'].append(f"Missing required columns: {', '.join(missing_columns)}")
                
                # Get sample data (first 5 rows)
                validation_result['sample_data'] = products_data[:5]
            
            # Validate each row
            valid_rows = 0
            for i, row in enumerate(products_data):
                is_valid, row_errors = self._validate_csv_row(row)
                if is_valid:
                    valid_rows += 1
                else:
                    if len(validation_result['errors']) < 10:  # Limit error messages
                        validation_result['errors'].extend([f"Row {i+1}: {error}" for error in row_errors])
            
            validation_result['valid_rows'] = valid_rows
            
            # Overall validation
            if validation_result['valid_rows'] > 0 and not validation_result['errors']:
                validation_result['valid'] = True
            
            # Add warnings
            if valid_rows < len(products_data):
                validation_result['warnings'].append(f"{len(products_data) - valid_rows} rows have validation issues")
            
            return validation_result
            
        except Exception as e:
            validation_result['errors'].append(f"File validation error: {str(e)}")
            return validation_result
    
    def generate_sample_csv(self, output_path: str) -> bool:
        """Generate sample CSV file with correct format"""
        try:
            sample_data = [
                {
                    'name': 'فیلتر هوای پراید',
                    'price': '45000',
                    'description': 'فیلتر هوای اصلی برای خودروی پراید با کیفیت بالا',
                    'category': 'فیلتر و صافی',
                    'image': 'https://example.com/image1.jpg'
                },
                {
                    'name': 'روغن موتور 10W40',
                    'price': '120000',
                    'description': 'روغن موتور سینتتیک مناسب برای تمام فصول',
                    'category': 'روغن و مایعات',
                    'image': 'https://example.com/image2.jpg'
                },
                {
                    'name': 'لنت ترمز جلو پژو 206',
                    'price': '85000',
                    'description': 'لنت ترمز اصلی پژو 206 با ضمانت کیفیت',
                    'category': 'سیستم ترمز',
                    'image': 'https://example.com/image3.jpg'
                }
            ]
            
            with open(output_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                fieldnames = ['name', 'price', 'description', 'category', 'image']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                writer.writerows(sample_data)
            
            logger.info(f"Sample CSV file created: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating sample CSV: {e}")
            return False
    
    def get_import_stats(self) -> Dict:
        """Get import statistics from database"""
        try:
            with self.db_manager.get_session() as session:
                total_products = session.query(Product).count()
                mapped_products = session.query(Product).filter(
                    Product.woocommerce_id.isnot(None)
                ).count()
                active_products = session.query(Product).filter(
                    Product.is_active == True
                ).count()
                
                return {
                    'total_products_in_db': total_products,
                    'products_mapped_to_wc': mapped_products,
                    'active_products': active_products,
                    'mapping_percentage': (mapped_products / total_products * 100) if total_products > 0 else 0
                }
                
        except Exception as e:
            logger.error(f"Error getting import stats: {e}")
            return {}
