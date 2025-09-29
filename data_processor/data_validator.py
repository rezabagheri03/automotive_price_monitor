"""
Data validation and cleaning utilities
"""
import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import pandas as pd
from database.models import Product, PriceHistory
from config.database import db_manager
from utils.logger import setup_logger

logger = setup_logger(__name__)


class DataValidator:
    """Validate and clean scraped data"""
    
    def __init__(self):
        self.db_manager = db_manager
        self.validation_rules = self._load_validation_rules()
    
    def _load_validation_rules(self) -> Dict:
        """Load validation rules configuration"""
        return {
            'price': {
                'min_value': 1000,  # Minimum price in IRR
                'max_value': 100000000,  # Maximum price in IRR
                'required': True
            },
            'name': {
                'min_length': 3,
                'max_length': 255,
                'required': True,
                'patterns': {
                    'invalid_chars': r'[<>\"\'&]',  # Invalid characters
                    'html_tags': r'<[^>]+>',  # HTML tags
                }
            },
            'category': {
                'valid_categories': [
                    'اکتان و مکمل ها',
                    'رینگ و لاستیک', 
                    'سیستم خنک کننده',
                    'قطعات موتوری',
                    'لوازم جانبی خودرو',
                    'جلوبندی و تعلیق و سیستم فرمان',
                    'سوخت رسانی و احتراق و اگزوز',
                    'فیلتر و صافی',
                    'گیربکس و انتقال قدرت',
                    'لوازم مصرفی',
                    'روغن و مایعات',
                    'قطعات بدنه و داخل کابین',
                    'لوازم الکترونیک و سنسورها',
                    'سیستم ترمز'
                ]
            },
            'url': {
                'required': True,
                'pattern': r'^https?://[^\s]+$'
            }
        }
    
    def validate_product_data(self, product_data: Dict) -> Tuple[bool, List[str], Dict]:
        """Validate product data and return cleaned version"""
        errors = []
        cleaned_data = product_data.copy()
        
        # Validate name
        name_valid, name_errors, cleaned_name = self._validate_name(product_data.get('name'))
        if not name_valid:
            errors.extend(name_errors)
        else:
            cleaned_data['name'] = cleaned_name
        
        # Validate price
        price_valid, price_errors, cleaned_price = self._validate_price(product_data.get('price'))
        if not price_valid:
            errors.extend(price_errors)
        else:
            cleaned_data['price'] = cleaned_price
        
        # Validate category
        category_valid, category_errors, cleaned_category = self._validate_category(product_data.get('category'))
        if not category_valid:
            errors.extend(category_errors)
        else:
            cleaned_data['category'] = cleaned_category
        
        # Validate URL
        url_valid, url_errors, cleaned_url = self._validate_url(product_data.get('source_url'))
        if not url_valid:
            errors.extend(url_errors)
        else:
            cleaned_data['source_url'] = cleaned_url
        
        # Validate description
        if product_data.get('description'):
            cleaned_data['description'] = self._clean_description(product_data['description'])
        
        is_valid = len(errors) == 0
        return is_valid, errors, cleaned_data
    
    def _validate_name(self, name: Any) -> Tuple[bool, List[str], Optional[str]]:
        """Validate product name"""
        errors = []
        
        if not name:
            errors.append("Product name is required")
            return False, errors, None
        
        name = str(name).strip()
        
        # Check length
        if len(name) < self.validation_rules['name']['min_length']:
            errors.append(f"Product name too short (minimum {self.validation_rules['name']['min_length']} characters)")
        
        if len(name) > self.validation_rules['name']['max_length']:
            errors.append(f"Product name too long (maximum {self.validation_rules['name']['max_length']} characters)")
        
        # Check for invalid characters
        if re.search(self.validation_rules['name']['patterns']['invalid_chars'], name):
            errors.append("Product name contains invalid characters")
        
        # Remove HTML tags
        name = re.sub(self.validation_rules['name']['patterns']['html_tags'], '', name)
        
        # Clean extra whitespace
        name = ' '.join(name.split())
        
        return len(errors) == 0, errors, name
    
    def _validate_price(self, price: Any) -> Tuple[bool, List[str], Optional[float]]:
        """Validate product price"""
        errors = []
        
        if price is None:
            errors.append("Price is required")
            return False, errors, None
        
        try:
            # Convert to float
            if isinstance(price, str):
                # Clean price string
                price_cleaned = re.sub(r'[^\d.,]', '', price)
                price_cleaned = price_cleaned.replace(',', '')
                price = float(price_cleaned)
            else:
                price = float(price)
            
            # Check range
            if price < self.validation_rules['price']['min_value']:
                errors.append(f"Price too low (minimum {self.validation_rules['price']['min_value']} IRR)")
            
            if price > self.validation_rules['price']['max_value']:
                errors.append(f"Price too high (maximum {self.validation_rules['price']['max_value']} IRR)")
            
            return len(errors) == 0, errors, price
            
        except (ValueError, TypeError):
            errors.append("Invalid price format")
            return False, errors, None
    
    def _validate_category(self, category: Any) -> Tuple[bool, List[str], Optional[str]]:
        """Validate product category"""
        errors = []
        
        if not category:
            # Use default category
            return True, [], 'لوازم جانبی خودرو'
        
        category = str(category).strip()
        
        # Check if category is in valid list
        valid_categories = self.validation_rules['category']['valid_categories']
        
        # Try exact match first
        if category in valid_categories:
            return True, [], category
        
        # Try fuzzy matching
        category_lower = category.lower()
        for valid_cat in valid_categories:
            if category_lower in valid_cat.lower() or valid_cat.lower() in category_lower:
                return True, [], valid_cat
        
        # If no match found, use default
        logger.warning(f"Unknown category '{category}', using default")
        return True, [], 'لوازم جانبی خودرو'
    
    def _validate_url(self, url: Any) -> Tuple[bool, List[str], Optional[str]]:
        """Validate URL"""
        errors = []
        
        if not url:
            errors.append("URL is required")
            return False, errors, None
        
        url = str(url).strip()
        
        # Check URL format
        if not re.match(self.validation_rules['url']['pattern'], url):
            errors.append("Invalid URL format")
        
        return len(errors) == 0, errors, url
    
    def _clean_description(self, description: str) -> str:
        """Clean product description"""
        if not description:
            return ""
        
        # Remove HTML tags
        description = re.sub(r'<[^>]+>', '', description)
        
        # Clean extra whitespace
        description = ' '.join(description.split())
        
        # Limit length
        if len(description) > 1000:
            description = description[:997] + "..."
        
        return description
    
    def validate_price_history(self, price_data: List[Dict]) -> List[Dict]:
        """Validate and clean price history data"""
        validated_data = []
        
        for entry in price_data:
            try:
                # Validate required fields
                if not all(key in entry for key in ['product_id', 'site_name', 'price']):
                    logger.warning(f"Skipping price entry missing required fields: {entry}")
                    continue
                
                # Validate price
                price_valid, _, cleaned_price = self._validate_price(entry['price'])
                if not price_valid:
                    logger.warning(f"Skipping invalid price entry: {entry}")
                    continue
                
                # Clean data
                cleaned_entry = {
                    'product_id': int(entry['product_id']),
                    'site_name': str(entry['site_name']).strip(),
                    'price': cleaned_price,
                    'scraped_at': entry.get('scraped_at', datetime.utcnow()),
                    'currency': entry.get('currency', 'IRR'),
                    'availability': entry.get('availability', True)
                }
                
                validated_data.append(cleaned_entry)
                
            except Exception as e:
                logger.error(f"Error validating price entry {entry}: {e}")
                continue
        
        return validated_data
    
    def detect_duplicates(self, products: List[Dict]) -> List[Dict]:
        """Detect and mark duplicate products"""
        seen_products = set()
        duplicates = []
        
        for i, product in enumerate(products):
            # Create signature based on name similarity
            signature = self._create_product_signature(product.get('name', ''))
            
            if signature in seen_products:
                product['is_duplicate'] = True
                duplicates.append({
                    'index': i,
                    'product': product,
                    'signature': signature
                })
            else:
                seen_products.add(signature)
                product['is_duplicate'] = False
        
        logger.info(f"Detected {len(duplicates)} potential duplicates")
        return duplicates
    
    def _create_product_signature(self, name: str) -> str:
        """Create a signature for duplicate detection"""
        if not name:
            return ""
        
        # Normalize name
        name = name.lower().strip()
        
        # Remove common words and variations
        stop_words = ['قطعه', 'لوازم', 'یدکی', 'اصلی', 'درجه', 'یک', 'کیفیت', 'بالا']
        words = name.split()
        words = [word for word in words if word not in stop_words]
        
        # Sort words to handle order variations
        words.sort()
        
        return ' '.join(words)
    
    def validate_site_data_consistency(self, site_name: str) -> Dict:
        """Validate data consistency for a specific site"""
        try:
            with self.db_manager.get_session() as session:
                # Get recent data for the site
                recent_data = session.query(PriceHistory).filter(
                    PriceHistory.site_name == site_name,
                    PriceHistory.scraped_at >= datetime.utcnow() - pd.Timedelta(days=7)
                ).all()
                
                if not recent_data:
                    return {'status': 'no_data', 'message': 'No recent data found'}
                
                # Check for anomalies
                prices = [float(p.site_price) for p in recent_data if p.site_price]
                
                if not prices:
                    return {'status': 'no_prices', 'message': 'No valid prices found'}
                
                # Statistical analysis
                df = pd.DataFrame({'price': prices})
                stats = {
                    'mean': df['price'].mean(),
                    'std': df['price'].std(),
                    'median': df['price'].median(),
                    'min': df['price'].min(),
                    'max': df['price'].max(),
                    'count': len(prices)
                }
                
                # Detect anomalies
                anomalies = []
                
                # Check for extreme outliers (more than 3 standard deviations)
                if stats['std'] > 0:
                    outlier_threshold = 3 * stats['std']
                    outliers = df[abs(df['price'] - stats['mean']) > outlier_threshold]['price'].tolist()
                    if outliers:
                        anomalies.append(f"Found {len(outliers)} extreme price outliers")
                
                # Check for zero or negative prices
                invalid_prices = df[df['price'] <= 0]['price'].tolist()
                if invalid_prices:
                    anomalies.append(f"Found {len(invalid_prices)} invalid prices (≤0)")
                
                # Check for suspiciously high prices
                high_threshold = stats['median'] * 10  # 10x median
                high_prices = df[df['price'] > high_threshold]['price'].tolist()
                if high_prices:
                    anomalies.append(f"Found {len(high_prices)} suspiciously high prices")
                
                return {
                    'status': 'analyzed',
                    'stats': stats,
                    'anomalies': anomalies,
                    'quality_score': self._calculate_quality_score(stats, anomalies)
                }
                
        except Exception as e:
            logger.error(f"Error validating site data consistency: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _calculate_quality_score(self, stats: Dict, anomalies: List[str]) -> float:
        """Calculate data quality score (0-100)"""
        base_score = 100.0
        
        # Penalize for anomalies
        base_score -= len(anomalies) * 10
        
        # Penalize for high variance
        if stats['std'] > stats['mean'] * 0.5:  # High coefficient of variation
            base_score -= 20
        
        # Penalize for low data count
        if stats['count'] < 10:
            base_score -= 15
        
        return max(0.0, base_score)
    
    def clean_batch_data(self, data: List[Dict]) -> Tuple[List[Dict], Dict]:
        """Clean a batch of product data"""
        cleaned_data = []
        stats = {
            'total': len(data),
            'valid': 0,
            'invalid': 0,
            'duplicates': 0,
            'errors': []
        }
        
        # First pass: validate individual items
        for item in data:
            is_valid, errors, cleaned_item = self.validate_product_data(item)
            
            if is_valid:
                cleaned_data.append(cleaned_item)
                stats['valid'] += 1
            else:
                stats['invalid'] += 1
                stats['errors'].extend(errors)
        
        # Second pass: detect duplicates
        duplicates = self.detect_duplicates(cleaned_data)
        stats['duplicates'] = len(duplicates)
        
        # Remove duplicates
        cleaned_data = [item for item in cleaned_data if not item.get('is_duplicate', False)]
        
        logger.info(f"Data cleaning completed: {stats}")
        return cleaned_data, stats
