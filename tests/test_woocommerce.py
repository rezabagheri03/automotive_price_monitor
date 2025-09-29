"""
Tests for WooCommerce integration components
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from woocommerce_integration.api_client import WooCommerceClient
from woocommerce_integration.csv_importer import CSVImporter
from woocommerce_integration.batch_processor import BatchProcessor


class TestWooCommerceClient:
    """Test WooCommerceClient functionality"""
    
    @patch('woocommerce_integration.api_client.API')
    def test_client_initialization(self, mock_api):
        """Test WooCommerce client initialization"""
        with patch('woocommerce_integration.api_client.Config') as mock_config:
            mock_config.return_value.WOOCOMMERCE_URL = 'https://example.com'
            mock_config.return_value.WOOCOMMERCE_CONSUMER_KEY = 'test_key'
            mock_config.return_value.WOOCOMMERCE_CONSUMER_SECRET = 'test_secret'
            mock_config.return_value.WOOCOMMERCE_API_VERSION = 'wc/v3'
            
            client = WooCommerceClient()
            
            assert client.api is not None
            mock_api.assert_called_once()
    
    @patch('woocommerce_integration.api_client.API')
    def test_get_products(self, mock_api):
        """Test getting products from WooCommerce"""
        with patch('woocommerce_integration.api_client.Config'):
            client = WooCommerceClient()
            
            # Mock API response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = [
                {'id': 1, 'name': 'Test Product', 'price': '50.00'},
                {'id': 2, 'name': 'Test Product 2', 'price': '75.00'}
            ]
            
            client.api.get.return_value = mock_response
            
            products = client.get_products()
            
            assert len(products) == 2
            assert products[0]['name'] == 'Test Product'
            client.api.get.assert_called_with('products', params={'per_page': 100, 'page': 1})
    
    @patch('woocommerce_integration.api_client.API')
    def test_create_product(self, mock_api):
        """Test creating product in WooCommerce"""
        with patch('woocommerce_integration.api_client.Config'):
            client = WooCommerceClient()
            
            # Mock API response
            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.json.return_value = {
                'id': 123, 'name': 'New Product', 'status': 'publish'
            }
            
            client.api.post.return_value = mock_response
            
            product_data = {
                'name': 'New Product',
                'regular_price': '100.00',
                'status': 'publish'
            }
            
            result = client.create_product(product_data)
            
            assert result is not None
            assert result['id'] == 123
            assert result['name'] == 'New Product'


class TestCSVImporter:
    """Test CSVImporter functionality"""
    
    @patch('woocommerce_integration.csv_importer.WooCommerceClient')
    @patch('woocommerce_integration.csv_importer.db_manager')
    def test_csv_validation(self, mock_db_manager, mock_wc_client):
        """Test CSV file validation"""
        importer = CSVImporter()
        
        # Mock CSV data
        test_csv_content = [
            {'name': 'محصول تست', 'price': '50000', 'category': 'تست'},
            {'name': 'محصول دوم', 'price': '75000', 'category': 'تست'},
        ]
        
        with patch.object(importer, '_read_csv_file', return_value=test_csv_content):
            validation_result = importer.validate_csv_file('test.csv')
            
            assert validation_result['valid'] == True
            assert validation_result['total_rows'] == 2
            assert validation_result['valid_rows'] == 2
    
    @patch('woocommerce_integration.csv_importer.WooCommerceClient')
    def test_convert_to_woocommerce_format(self, mock_wc_client):
        """Test converting CSV data to WooCommerce format"""
        importer = CSVImporter()
        
        csv_data = {
            'name': 'محصول تست',
            'price': '50000',
            'description': 'توضیحات تست',
            'category': 'دسته تست',
            'image': 'https://example.com/image.jpg'
        }
        
        wc_data = importer._convert_to_woocommerce_format(csv_data)
        
        assert wc_data['name'] == 'محصول تست'
        assert wc_data['regular_price'] == '50000'
        assert wc_data['status'] == 'publish'
        assert len(wc_data['categories']) == 1
        assert wc_data['categories'][0]['name'] == 'دسته تست'


class TestBatchProcessor:
    """Test BatchProcessor functionality"""
    
    @patch('woocommerce_integration.batch_processor.WooCommerceClient')
    @patch('woocommerce_integration.batch_processor.db_manager')
    def test_batch_update_prices(self, mock_db_manager, mock_wc_client):
        """Test batch price updates"""
        processor = BatchProcessor()
        
        # Mock database data
        mock_session = Mock()
        mock_db_manager.get_session.return_value.__enter__.return_value = mock_session
        
        mock_result = [
            Mock(id=1, name='محصول ۱', woocommerce_id=101, avg_price=50000),
            Mock(id=2, name='محصول ۲', woocommerce_id=102, avg_price=75000),
        ]
        mock_session.execute.return_value.fetchall.return_value = mock_result
        
        # Mock WooCommerce client
        mock_wc_client.return_value.batch_update_products.return_value = {
            'success': 2, 'failed': 0, 'errors': []
        }
        
        results = processor.batch_update_prices()
        
        assert results['total_products'] == 2
        assert results['updated'] == 2
        assert results['failed'] == 0
    
    def test_process_price_batch(self):
        """Test processing a single price batch"""
        processor = BatchProcessor()
        
        batch_data = [
            {'id': 1, 'name': 'محصول ۱', 'woocommerce_id': 101, 'price': 50000},
            {'id': 2, 'name': 'محصول ۲', 'woocommerce_id': 102, 'price': 75000},
        ]
        
        with patch.object(processor.wc_client, 'batch_update_products') as mock_batch:
            mock_batch.return_value = {'success': 2, 'failed': 0, 'errors': []}
            
            results = processor._process_price_batch(batch_data, 'avg')
            
            assert results['processed'] == 2
            assert results['updated'] == 2
            assert results['failed'] == 0


def test_product_data_validation():
    """Test product data validation for WooCommerce"""
    from woocommerce_integration.api_client import WooCommerceClient
    
    with patch('woocommerce_integration.api_client.Config'):
        client = WooCommerceClient()
        
        # Test valid data
        valid_data = {
            'name': 'محصول تست',
            'regular_price': '50000',
            'sku': 'TEST-001'
        }
        
        is_valid, errors = client.validate_product_data(valid_data)
        assert is_valid == True
        assert len(errors) == 0
        
        # Test invalid data
        invalid_data = {
            'name': '',  # Missing name
            'regular_price': '-100',  # Negative price
        }
        
        is_valid, errors = client.validate_product_data(invalid_data)
        assert is_valid == False
        assert len(errors) > 0


@pytest.fixture
def sample_csv_data():
    """Sample CSV data for testing"""
    return [
        {
            'name': 'محصول تست ۱',
            'price': '50000',
            'description': 'توضیحات محصول تست',
            'category': 'دسته تست',
            'image': 'https://example.com/image1.jpg'
        },
        {
            'name': 'محصول تست ۲',
            'price': '75000',
            'description': 'توضیحات محصول دوم',
            'category': 'دسته تست',
            'image': 'https://example.com/image2.jpg'
        }
    ]
