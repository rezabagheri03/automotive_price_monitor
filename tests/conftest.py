"""
Pytest configuration and fixtures
"""
import pytest
import tempfile
import os
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add project root to path
import sys
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from config.database import Base, DatabaseManager
from database.models import Product, PriceHistory, User, SiteConfig
from dashboard.app import create_app


@pytest.fixture
def app():
    """Create application for testing"""
    app = create_app('testing')
    app.config.update({
        'TESTING': True,
        'WTF_CSRF_ENABLED': False
    })
    
    with app.app_context():
        yield app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def test_db():
    """Create test database"""
    # Create temporary database
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    session.close()


@pytest.fixture
def sample_product(test_db):
    """Create sample product for testing"""
    product = Product(
        name='تست محصول',
        sku='TEST-001',
        category='لوازم جانبی خودرو',
        description='این یک محصول تست است',
        is_active=True,
        is_monitored=True,
        created_at=datetime.utcnow()
    )
    test_db.add(product)
    test_db.commit()
    
    return product


@pytest.fixture
def sample_price_history(test_db, sample_product):
    """Create sample price history"""
    price_entries = [
        PriceHistory(
            product_id=sample_product.id,
            site_name='test-site',
            site_price=50000,
            avg_price=50000,
            min_price=45000,
            max_price=55000,
            price_count=3,
            scraped_at=datetime.utcnow()
        )
    ]
    
    for entry in price_entries:
        test_db.add(entry)
    test_db.commit()
    
    return price_entries


@pytest.fixture
def test_user(test_db):
    """Create test user"""
    user = User(
        username='testuser',
        email='test@example.com',
        role='admin',
        is_active=True,
        created_at=datetime.utcnow()
    )
    user.set_password('testpass123')
    
    test_db.add(user)
    test_db.commit()
    
    return user
