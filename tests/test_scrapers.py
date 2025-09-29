"""
Tests for scraper components
"""
import pytest
from unittest.mock import Mock, patch
from scrapy.http import HtmlResponse, Request
from scrapers.automotive_scraper.spiders.autonik_spider import AutonikSpider
from scrapers.automotive_scraper.items import AutomotiveProductItem
from scrapers.automotive_scraper.pipelines import ValidationPipeline, DatabasePipeline


class TestAutonikSpider:
    """Test AutonikSpider functionality"""
    
    def test_spider_initialization(self):
        """Test spider initialization"""
        spider = AutonikSpider()
        assert spider.name == 'autonik'
        assert spider.site_name == 'auto-nik.com'
        assert 'auto-nik.com' in spider.allowed_domains
    
    def test_parse_product_page(self):
        """Test product page parsing"""
        spider = AutonikSpider()
        
        # Mock response
        html_content = """
        <html>
            <body>
                <h1 class="entry-title">تست محصول ABS</h1>
                <div class="woocommerce-Price-amount">
                    <bdi>45,000</bdi>
                </div>
                <div class="product-description">توضیحات محصول تست</div>
                <div class="stock">موجود</div>
            </body>
        </html>
        """
        
        response = HtmlResponse(
            url='https://auto-nik.com/product/test-abs/',
            body=html_content.encode('utf-8')
        )
        
        # Parse product
        results = list(spider.parse_product(response))
        
        assert len(results) == 1
        item = results[0]
        assert isinstance(item, AutomotiveProductItem)
        assert item['name'] == 'تست محصول ABS'
        assert item['price'] == 45000
        assert item['site_name'] == 'auto-nik.com'


class TestValidationPipeline:
    """Test ValidationPipeline"""
    
    def test_valid_item_processing(self):
        """Test processing of valid item"""
        pipeline = ValidationPipeline()
        spider = Mock()
        
        item = AutomotiveProductItem()
        item['name'] = 'تست محصول'
        item['price'] = 50000
        item['site_name'] = 'test-site'
        item['source_url'] = 'https://test-site.com/product/1'
        
        result = pipeline.process_item(item, spider)
        
        assert result == item
        assert pipeline.processed_items == 1
    
    def test_invalid_item_rejection(self):
        """Test rejection of invalid item"""
        pipeline = ValidationPipeline()
        spider = Mock()
        
        item = AutomotiveProductItem()
        item['name'] = ''  # Invalid: empty name
        item['price'] = -1000  # Invalid: negative price
        
        with pytest.raises(Exception):
            pipeline.process_item(item, spider)


class TestDatabasePipeline:
    """Test DatabasePipeline"""
    
    @patch('scrapers.automotive_scraper.pipelines.db_manager')
    def test_save_product(self, mock_db_manager):
        """Test saving product to database"""
        pipeline = DatabasePipeline()
        spider = Mock()
        
        # Mock database session
        mock_session = Mock()
        mock_db_manager.get_session.return_value.__enter__.return_value = mock_session
        
        item = AutomotiveProductItem()
        item['name'] = 'تست محصول'
        item['price'] = 50000
        item['site_name'] = 'test-site'
        item['source_url'] = 'https://test-site.com/product/1'
        item['scraped_at'] = pytest.datetime.utcnow()
        
        result = pipeline.process_item(item, spider)
        
        assert result == item
        mock_session.add.assert_called()


def test_price_cleaning():
    """Test price cleaning functionality"""
    from scrapers.automotive_scraper.items import clean_price
    
    test_cases = [
        ('45,000 ریال', 45000),
        ('۱۲۳,۴۵۶', 123456),
        ('ABC 50000 DEF', 50000),
        ('', None),
        ('invalid', None),
    ]
    
    for input_price, expected in test_cases:
        result = clean_price(input_price)
        assert result == expected, f"Expected {expected} for input '{input_price}', got {result}"


def test_url_cleaning():
    """Test URL cleaning functionality"""
    from scrapers.automotive_scraper.items import clean_url
    
    test_cases = [
        ('https://example.com/path', 'https://example.com/path'),
        ('http://example.com', 'http://example.com'),
        ('invalid-url', None),
        ('', None),
    ]
    
    for input_url, expected in test_cases:
        result = clean_url(input_url)
        assert result == expected
