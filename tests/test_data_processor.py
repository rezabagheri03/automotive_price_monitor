"""
Tests for data processor components
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from data_processor.price_calculator import PriceCalculator
from data_processor.data_validator import DataValidator
from data_processor.csv_generator import CSVGenerator
from data_processor.cache_manager import CacheManager


class TestPriceCalculator:
    """Test PriceCalculator functionality"""
    
    @patch('data_processor.price_calculator.db_manager')
    def test_calculate_daily_prices(self, mock_db_manager):
        """Test daily price calculation"""
        calculator = PriceCalculator()
        
        # Mock database data
        mock_session = Mock()
        mock_db_manager.get_session.return_value.__enter__.return_value = mock_session
        
        # Mock price history data
        mock_price_data = [
            Mock(product_id=1, site_price=45000),
            Mock(product_id=1, site_price=47000),
            Mock(product_id=1, site_price=46000),
        ]
        mock_session.query.return_value.filter.return_value.all.return_value = mock_price_data
        
        results = calculator.calculate_daily_prices()
        
        assert isinstance(results, dict)
        assert 1 in results
        product_stats = results[1]
        assert 'avg_price' in product_stats
        assert 'min_price' in product_stats
        assert 'max_price' in product_stats
    
    def test_remove_outliers(self):
        """Test outlier removal"""
        calculator = PriceCalculator()
        import numpy as np
        
        # Test data with outliers
        prices = np.array([45000, 46000, 47000, 100000, 48000])  # 100000 is outlier
        
        cleaned, outliers_count = calculator._remove_outliers(prices)
        
        assert len(cleaned) < len(prices)
        assert outliers_count == 1


class TestDataValidator:
    """Test DataValidator functionality"""
    
    def test_validate_product_data_valid(self):
        """Test validation of valid product data"""
        validator = DataValidator()
        
        product_data = {
            'name': 'محصول تست',
            'price': 50000,
            'category': 'لوازم جانبی خودرو',
            'source_url': 'https://example.com/product/1'
        }
        
        is_valid, errors, cleaned_data = validator.validate_product_data(product_data)
        
        assert is_valid == True
        assert len(errors) == 0
        assert cleaned_data['name'] == 'محصول تست'
        assert cleaned_data['price'] == 50000.0
    
    def test_validate_product_data_invalid(self):
        """Test validation of invalid product data"""
        validator = DataValidator()
        
        product_data = {
            'name': '',  # Invalid: empty name
            'price': -1000,  # Invalid: negative price
            'category': 'invalid_category',
            'source_url': 'not-a-url'
        }
        
        is_valid, errors, cleaned_data = validator.validate_product_data(product_data)
        
        assert is_valid == False
        assert len(errors) > 0
        assert 'Product name is required' in errors
        assert 'Price too low' in errors
    
    def test_detect_duplicates(self):
        """Test duplicate detection"""
        validator = DataValidator()
        
        products = [
            {'name': 'محصول تست ۱'},
            {'name': 'محصول تست 1'},  # Similar name (duplicate)
            {'name': 'محصول متفاوت'},
        ]
        
        duplicates = validator.detect_duplicates(products)
        
        assert len(duplicates) >= 1  # At least one duplicate detected


class TestCSVGenerator:
    """Test CSVGenerator functionality"""
    
    @patch('data_processor.csv_generator.db_manager')
    def test_generate_woocommerce_csv(self, mock_db_manager):
        """Test WooCommerce CSV generation"""
        generator = CSVGenerator()
        
        # Mock database session and data
        mock_session = Mock()
        mock_db_manager.get_session.return_value.__enter__.return_value = mock_session
        
        # Mock query results
        mock_result = [
            Mock(id=1, name='تست محصول', avg_price=50000, category='تست', 
                 description='توضیحات', image_url='http://test.jpg', sku='TEST-001')
        ]
        mock_session.execute.return_value.fetchall.return_value = mock_result
        
        with patch('os.path.join'), patch('builtins.open'), patch('csv.DictWriter'):
            csv_path = generator.generate_woocommerce_csv()
            assert csv_path.endswith('.csv')
    
    def test_get_product_status(self):
        """Test product status determination"""
        generator = CSVGenerator()
        
        # Test active product with prices
        row = Mock(is_active=True, is_monitored=True, avg_price=50000, 
                  site_count=3, last_updated=datetime.utcnow())
        
        status = generator._get_product_status(row)
        assert status == 'OK'
        
        # Test inactive product
        row.is_active = False
        status = generator._get_product_status(row)
        assert status == 'Inactive'


class TestCacheManager:
    """Test CacheManager functionality"""
    
    def test_memory_cache_operations(self):
        """Test memory cache operations"""
        cache = CacheManager()
        # Force memory cache mode
        cache.redis_client = None
        
        # Test set and get
        cache.set('test_key', {'data': 'test_value'}, ttl=60)
        result = cache.get('test_key')
        
        assert result is not None
        assert result['data'] == 'test_value'
        
        # Test delete
        success = cache.delete('test_key')
        assert success == True
        
        result = cache.get('test_key')
        assert result is None
    
    def test_cache_expiry(self):
        """Test cache expiry functionality"""
        cache = CacheManager()
        cache.redis_client = None  # Force memory cache
        
        # Set with very short TTL
        cache.set('expire_test', 'value', ttl=0.1)
        
        # Should exist immediately
        result = cache.get('expire_test')
        assert result == 'value'
        
        # Wait for expiry and cleanup
        import time
        time.sleep(0.2)
        cache.cleanup_expired()
        
        # Should be expired
        result = cache.get('expire_test')
        assert result is None
    
    def test_get_or_set(self):
        """Test get_or_set functionality"""
        cache = CacheManager()
        cache.redis_client = None
        
        callback_called = False
        
        def callback():
            nonlocal callback_called
            callback_called = True
            return {'computed': 'value'}
        
        # First call should execute callback
        result = cache.get_or_set('computed_key', callback, ttl=60)
        assert callback_called == True
        assert result['computed'] == 'value'
        
        # Second call should use cached value
        callback_called = False
        result = cache.get_or_set('computed_key', callback, ttl=60)
        assert callback_called == False
        assert result['computed'] == 'value'
