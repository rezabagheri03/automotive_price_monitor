"""
Database models for the Automotive Price Monitor system
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DECIMAL, DateTime, Boolean, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from werkzeug.security import generate_password_hash, check_password_hash
from config.database import Base


class Product(Base):
    """Product model for storing automotive parts information"""
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    sku = Column(String(100), unique=True, index=True)
    category = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    image_url = Column(String(500))
    
    # WooCommerce integration
    woocommerce_id = Column(Integer, index=True)
    woocommerce_sku = Column(String(100), index=True)
    
    # Site URLs where this product can be found
    site_urls = Column(JSON)  # {"site_name": "url", ...}
    
    # Status flags
    is_active = Column(Boolean, default=True, index=True)
    is_monitored = Column(Boolean, default=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_scraped = Column(DateTime, index=True)
    
    # Relationships
    price_history = relationship("PriceHistory", back_populates="product", cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_product_category_active', 'category', 'is_active'),
        Index('idx_product_name_category', 'name', 'category'),
        Index('idx_product_updated_monitored', 'updated_at', 'is_monitored'),
    )
    
    @hybrid_property
    def latest_prices(self):
        """Get the latest price data for this product"""
        if self.price_history:
            return sorted(self.price_history, key=lambda p: p.scraped_at, reverse=True)[0]
        return None
    
    @hybrid_property
    def current_avg_price(self):
        """Get current average price"""
        latest = self.latest_prices
        return latest.avg_price if latest else None
    
    @hybrid_property
    def current_min_price(self):
        """Get current minimum price"""
        latest = self.latest_prices
        return latest.min_price if latest else None
    
    @hybrid_property
    def current_max_price(self):
        """Get current maximum price"""
        latest = self.latest_prices
        return latest.max_price if latest else None
    
    def __repr__(self):
        return f'<Product {self.name} ({self.sku})>'


class PriceHistory(Base):
    """Price history model for storing scraped price data"""
    __tablename__ = 'price_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False, index=True)
    
    # Individual site prices
    site_name = Column(String(100), nullable=False, index=True)
    site_price = Column(DECIMAL(10, 2))
    site_url = Column(String(500))
    site_availability = Column(Boolean, default=True)
    
    # Calculated prices (for the day)
    avg_price = Column(DECIMAL(10, 2), index=True)
    min_price = Column(DECIMAL(10, 2), index=True)
    max_price = Column(DECIMAL(10, 2), index=True)
    price_count = Column(Integer, default=0)  # Number of sites with prices
    
    # Metadata
    currency = Column(String(10), default='IRR')
    scraped_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    product = relationship("Product", back_populates="price_history")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_price_product_date', 'product_id', 'scraped_at'),
        Index('idx_price_site_date', 'site_name', 'scraped_at'),
        Index('idx_price_avg_date', 'avg_price', 'scraped_at'),
    )
    
    def __repr__(self):
        return f'<PriceHistory {self.product_id} - {self.site_name}: {self.site_price}>'


class ScrapingLog(Base):
    """Scraping log model for monitoring scraping activities"""
    __tablename__ = 'scraping_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Scraping session info
    session_id = Column(String(50), nullable=False, index=True)
    site_name = Column(String(100), nullable=False, index=True)
    spider_name = Column(String(100), nullable=False)
    
    # Status and results
    status = Column(String(20), nullable=False, index=True)  # started, completed, failed, cancelled
    products_found = Column(Integer, default=0)
    products_scraped = Column(Integer, default=0)
    prices_extracted = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)
    
    # Performance metrics
    start_time = Column(DateTime, default=datetime.utcnow, index=True)
    end_time = Column(DateTime, index=True)
    duration_seconds = Column(Integer)
    pages_scraped = Column(Integer, default=0)
    requests_made = Column(Integer, default=0)
    
    # Error information
    error_message = Column(Text)
    error_details = Column(JSON)
    
    # User who initiated (for manual runs)
    initiated_by = Column(String(100))
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_log_session_site', 'session_id', 'site_name'),
        Index('idx_log_status_time', 'status', 'start_time'),
        Index('idx_log_site_time', 'site_name', 'start_time'),
    )
    
    @hybrid_property
    def success_rate(self):
        """Calculate success rate as percentage"""
        if self.products_found > 0:
            return (self.products_scraped / self.products_found) * 100
        return 0
    
    def __repr__(self):
        return f'<ScrapingLog {self.session_id} - {self.site_name}: {self.status}>'


class SiteConfig(Base):
    """Site configuration model for storing scraping parameters"""
    __tablename__ = 'site_configs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    site_name = Column(String(100), unique=True, nullable=False, index=True)
    base_url = Column(String(255), nullable=False)
    
    # Scraping configuration
    selectors = Column(JSON)  # CSS/XPath selectors for different elements
    request_delay = Column(DECIMAL(3, 1), default=2.0)
    concurrent_requests = Column(Integer, default=5)
    user_agent = Column(String(500))
    
    # Site-specific settings
    requires_javascript = Column(Boolean, default=False)
    uses_pagination = Column(Boolean, default=True)
    max_pages = Column(Integer, default=100)
    
    # Authentication if needed
    requires_auth = Column(Boolean, default=False)
    auth_config = Column(JSON)  # Login credentials or API keys
    
    # Status flags
    is_active = Column(Boolean, default=True, index=True)
    is_available = Column(Boolean, default=True, index=True)
    
    # Monitoring
    last_successful_scrape = Column(DateTime, index=True)
    consecutive_failures = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<SiteConfig {self.site_name}>'


class User(Base):
    """User model for dashboard authentication"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(80), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(128))
    
    # User info
    first_name = Column(String(50))
    last_name = Column(String(50))
    role = Column(String(20), default='user', index=True)  # admin, user, viewer
    
    # Status flags
    is_active = Column(Boolean, default=True, index=True)
    is_verified = Column(Boolean, default=False)
    
    # Login tracking
    last_login = Column(DateTime)
    login_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    @hybrid_property
    def full_name(self):
        """Get full name"""
        return f"{self.first_name or ''} {self.last_name or ''}".strip()
    
    @hybrid_property
    def is_admin(self):
        """Check if user is admin"""
        return self.role == 'admin'
    
    def __repr__(self):
        return f'<User {self.username}>'
